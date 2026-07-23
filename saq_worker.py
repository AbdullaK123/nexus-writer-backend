from saq import Queue
from saq.types import Context, JobTaskContext
from src.app.dependencies.services import build_ai_provider
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.scene import SceneRepository
from src.infrastructure.config.settings import settings as app_settings
from src.infrastructure.db.pool import init_pool, close_pool
from src.infrastructure.telemetry.logfire import init_tracing
from src.service.embedding.service import EmbeddingService
from src.service.extraction.service import ExtractionService
from src.infrastructure.redis.queue import queue
from dotenv import load_dotenv
from src.shared.utils.logging import configure_logger
from pathlib import Path
import asyncio
from opentelemetry import trace
from loguru import logger

load_dotenv()
configure_logger()
init_tracing("nexus-saq-worker")

HEARTBEAT_FILE = Path("/tmp/saq_worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30

tracer = trace.get_tracer(__name__)

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

    extraction_service = ExtractionService(
        provider=provider,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo
    )
    embedding_service = EmbeddingService(
        scene_repo=scene_repo,
        provider=provider
    )

    heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    ctx['heartbeat_task'] = heartbeat_task
    ctx['extraction_service'] = extraction_service
    ctx['embedding_service'] = embedding_service

    logger.info("Startup complete!")


async def shutdown(ctx: Context) -> None:

    logger.info("Shutting down SAQ worker...")

    task = ctx['heartbeat_task']
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    await close_pool()

    logger.info("Goodbye...")

async def scene_and_embedding_job(ctx: Context, *, chapter_id: str) -> None:
    with tracer.start_as_current_span("saq.scene_and_embedding_job") as span:
        try:
            await ctx['worker'].context['extraction_service'].extract_scenes(chapter_id)
            await ctx['worker'].context['embedding_service'].embed_scenes(chapter_id)
            span.set_status(trace.StatusCode.OK)
        except Exception as e:
            logger.exception("saq.scene_and_embedding_job.failed")
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
        finally:
            HEARTBEAT_FILE.touch()
            

settings = {
    "queue": queue,
    "functions": [
        scene_and_embedding_job
    ],
    "concurrency": 5,
    "startup": startup,
    "shutdown": shutdown
}


