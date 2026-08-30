from typing import Optional
from uuid import UUID

from saq.types import Context
from src.app.dependencies.redis import get_redis
from src.app.dependencies.services import build_ai_provider
from src.data.repositories.analytics import AnalyticsRepository
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.scene import SceneRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.auth import Notification
from src.data.schemas.extraction import CommentExtractionResponse, SceneExtractionResult
from src.infrastructure.db.pool import init_pool, close_pool
from src.infrastructure.redis.pubsub import RedisPubSub
from src.infrastructure.redis.queue import client
from src.infrastructure.config.settings import config, settings as app_settings
from src.infrastructure.telemetry.logfire import init_tracing
from src.service.analytics.service import AnalyticsService
from src.service.chapter.service import ChapterService
from src.service.embedding.service import EmbeddingService
from src.service.extraction.service import ExtractionService
from src.infrastructure.redis.queue import queue
from dotenv import load_dotenv
from src.service.story.service import StoryService
from src.shared.utils.logging import configure_logger
from pathlib import Path
import asyncio
import hashlib
from opentelemetry import trace
from loguru import logger

load_dotenv()
configure_logger()
init_tracing("nexus-saq-worker")

HEARTBEAT_FILE = Path("/tmp/saq_worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30
SCENE_JOB_COMPLETION_TTL_SECONDS = 7 * 24 * 60 * 60

tracer = trace.get_tracer(__name__)


def _validate_job_ids(**ids: str) -> None:
    for name, value in ids.items():
        try:
            UUID(value)
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid {name}") from exc


def _scene_job_completion_key(chapter_id: str, content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"chapter:extraction-complete:{chapter_id}:{digest}"


async def heartbeat_loop() -> None:
    while True:
        HEARTBEAT_FILE.touch()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


async def startup(ctx: Context) -> None:
    logger.info("Starting SAQ worker...")

    pool = await init_pool()
    provider = build_ai_provider()
    chapter_repo = ChapterRepository(pool)
    scene_repo = SceneRepository(pool)
    story_repo = StoryRepository(pool)
    analytics_repo = AnalyticsRepository(pool)
    pubsub = RedisPubSub(client)

    extraction_service = ExtractionService(
        provider=provider,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo,
    )
    embedding_service = EmbeddingService(
        scene_repo=scene_repo,
        provider=provider,
    )
    story_service = StoryService(
        story_repo=story_repo,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo,
        provider=provider,
        search_config=config.search,
        redis=client,
    )
    chapter_service = ChapterService(
        story_repo=story_repo,
        chapter_repo=chapter_repo,
        analytics_repo=analytics_repo,
        scene_repo=scene_repo,
        provider=provider,
        redis=client,
    )
    analytics_service = AnalyticsService(
        analytics_repo=analytics_repo,
        story_repo=story_repo,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo,
        provider=provider,
        redis=client,
    )

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    ctx["chapter_repo"] = chapter_repo
    ctx["heartbeat_task"] = heartbeat_task
    ctx["extraction_service"] = extraction_service
    ctx["embedding_service"] = embedding_service
    ctx["story_service"] = story_service
    ctx["chapter_service"] = chapter_service
    ctx["analytics_service"] = analytics_service
    ctx["pubsub"] = pubsub

    logger.info("Startup complete!")


async def shutdown(ctx: Context) -> None:
    logger.info("Shutting down SAQ worker...")

    task = ctx["heartbeat_task"]
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    await close_pool()
    logger.info("Goodbye...")


async def story_reanalysis_job(
    ctx: Context, *, story_id: str, user_id: str, story_title: str
) -> None:
    _validate_job_ids(story_id=story_id, user_id=user_id)

    with tracer.start_as_current_span("saq.story_reanalysis_job") as span:
        try:
            await asyncio.gather(
                ctx["worker"].context["story_service"].get_pulse(
                    user_id=user_id,
                    story_id=story_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_plot_threads(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_acts(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_contradictions(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_entities(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
            )

            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="analysis_ready",
                    story_id=story_id,
                    chapter_id="",
                    message=f"New pulse and analysis for {story_title} are ready.",
                ),
            )
            span.set_status(trace.StatusCode.OK)
        except Exception as e:
            logger.exception("saq.story_reanalysis_job.failed")
            span.record_exception(e)
            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="job_failed",
                    story_id=story_id,
                    chapter_id="",
                    message=f"Analysis job for {story_title} has failed. The server might be experiencing issues.",
                ),
            )
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
        finally:
            await client.delete(f"story:reanalysis-pending:{story_id}")
            HEARTBEAT_FILE.touch()


async def chapter_reanalysis_job(
    ctx: Context, *, chapter_id: str, story_id: str, user_id: str
) -> None:
    _validate_job_ids(chapter_id=chapter_id, story_id=story_id, user_id=user_id)

    with tracer.start_as_current_span("saq.chapter_reanalysis_job") as span:
        try:
            chapter = await ctx["worker"].context["chapter_repo"].get(chapter_id, user_id)

            if chapter is None or not chapter.published:
                return

            if chapter.story_id != story_id:
                raise ValueError("Chapter does not belong to story")

            await ctx["worker"].context["chapter_service"].summarize_chapter(
                user_id=user_id,
                chapter_id=chapter_id,
                ignore_cache=True,
            )

            comments_extraction: CommentExtractionResponse = await ctx["worker"].context[
                "chapter_service"
            ].generate_comments(
                user_id,
                chapter_id,
                ignore_cache=True,
            )

            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="comments_ready",
                    story_id=story_id,
                    chapter_id=chapter_id,
                    message=f"{len(comments_extraction.extraction.comments)} comments are ready for chapter {comments_extraction.chapter_number} of {comments_extraction.story_title}",
                ),
            )
            span.set_status(trace.StatusCode.OK)
        except ValueError:
            raise
        except Exception as e:
            logger.exception("saq.chapter_reanalysis_job.failed")
            span.record_exception(e)
            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="job_failed",
                    story_id=story_id,
                    chapter_id="",
                    message="Chapter analysis job has failed. The server might be experiencing issues.",
                ),
            )
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
        finally:
            await client.delete(f"chapter:chapter-reanalysis-pending:{chapter_id}")
            HEARTBEAT_FILE.touch()


async def scene_and_embedding_job(
    ctx: Context,
    *,
    chapter_id: str,
    story_id: str,
    user_id: str,
    content: str | None = None,
) -> None:
    _validate_job_ids(chapter_id=chapter_id, story_id=story_id, user_id=user_id)

    with tracer.start_as_current_span("saq.scene_and_embedding_job") as span:
        try:
            chapter = await ctx["worker"].context["chapter_repo"].get(chapter_id, user_id)

            if chapter is None or not chapter.published:
                return

            if chapter.story_id != story_id:
                raise ValueError("Chapter does not belong to story")

            baseline_content = chapter.content or ""
            completion_key = _scene_job_completion_key(chapter_id, baseline_content)
            if await client.get(completion_key):
                logger.info(
                    "saq.scene_and_embedding_job.redelivery_skipped",
                    chapter_id=chapter_id,
                )
                return

            result: Optional[SceneExtractionResult] = await ctx["worker"].context[
                "extraction_service"
            ].extract_scenes(
                chapter_id,
                user_id,
                baseline_content,
            )

            current_chapter = await ctx["worker"].context["chapter_repo"].get(
                chapter_id,
                user_id,
            )

            if current_chapter is None or not current_chapter.published:
                return

            if current_chapter.story_id != story_id:
                raise ValueError("Chapter does not belong to story")

            if (current_chapter.content or "") != baseline_content:
                return

            await ctx["worker"].context["embedding_service"].embed_scenes(chapter_id)

            if result:
                await ctx["worker"].context["pubsub"].publish(
                    f"notifications:{user_id}",
                    Notification(
                        kind="scenes_extracted",
                        story_id=story_id,
                        chapter_id=chapter_id,
                        message=f"Extracted {result.scenes_extracted} scenes from Chapter {result.chapter_number} of {result.story_title}",
                    ),
                )

            await client.set(f"chapter:baseline:{chapter_id}", baseline_content)
            await client.delete(f"chapter:extraction-pending:{chapter_id}")

            await asyncio.gather(
                ctx["worker"].context["story_service"].get_pulse(
                    user_id=user_id,
                    story_id=story_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["chapter_service"].summarize_chapter(
                    user_id=user_id,
                    chapter_id=chapter_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_plot_threads(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_acts(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_contradictions(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
                ctx["worker"].context["analytics_service"].extract_entities(
                    story_id=story_id,
                    user_id=user_id,
                    ignore_cache=True,
                ),
            )

            if result:
                await ctx["worker"].context["pubsub"].publish(
                    f"notifications:{user_id}",
                    Notification(
                        kind="analysis_ready",
                        story_id=story_id,
                        chapter_id=chapter_id,
                        message=f"New pulse and analysis for {result.story_title} are ready.",
                    ),
                )

            comments_extraction: CommentExtractionResponse = await ctx["worker"].context[
                "chapter_service"
            ].generate_comments(
                user_id,
                chapter_id,
                ignore_cache=True,
            )

            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="comments_ready",
                    story_id=story_id,
                    chapter_id=chapter_id,
                    message=f"{len(comments_extraction.extraction.comments)} comments are ready for chapter {comments_extraction.chapter_number} of {comments_extraction.story_title}",
                ),
            )

            await client.set(
                completion_key,
                "1",
                ex=SCENE_JOB_COMPLETION_TTL_SECONDS,
            )
            span.set_status(trace.StatusCode.OK)
        except ValueError:
            raise
        except Exception as e:
            logger.exception("saq.scene_and_embedding_job.failed")
            span.record_exception(e)
            await ctx["worker"].context["pubsub"].publish(
                f"notifications:{user_id}",
                Notification(
                    kind="job_failed",
                    story_id=story_id,
                    chapter_id="",
                    message="Extraction job failed. The server might be experiencing issues.",
                ),
            )
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
        finally:
            await client.delete(f"chapter:extraction-pending:{chapter_id}")
            HEARTBEAT_FILE.touch()


settings = {
    "queue": queue,
    "functions": [
        scene_and_embedding_job,
        chapter_reanalysis_job,
        story_reanalysis_job,
    ],
    "concurrency": 5,
    "startup": startup,
    "shutdown": shutdown,
}
