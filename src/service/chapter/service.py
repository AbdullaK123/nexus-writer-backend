from __future__ import annotations
import textwrap
from typing import TYPE_CHECKING, List, Optional, Union

import asyncpg
from loguru import logger
from pydantic_ai import Agent

from src.data.repositories import (
    StoryRepository,
    ChapterRepository,
    SceneRepository,
)
from src.data.repositories.analytics import AnalyticsRepository
from src.data.schemas import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse,
)
from src.data.schemas.chapter import ChapterSummaryResponse
from src.data.schemas.enums import StoryStatus
from src.data.schemas.extraction import CommentExtraction, CommentExtractionResponse
from src.data.schemas.scene import SceneRow
from src.infrastructure.config import config
from src.infrastructure.ai.prompts import COMMENTS_EXTRACTION_PROMPT, COMMENTS_PLANNER_PROMPT, SUMMARIZATION_PROMPT
from src.infrastructure.ai.providers.protocol import AIProvider
from src.service.exceptions import NotFoundError, ValidationError, InternalError, ConflictError
from src.service.utils.decorators import handle_service_errors
from functools import cached_property, lru_cache
from src.infrastructure.redis.queue import queue
from datetime import datetime, timezone as tz
from datetime import timedelta
import redis.asyncio as aioredis
from src.shared.utils.html import (
    get_similarity_ratio,
    get_preview_content,
    get_word_count,
    html_to_plain_text,
)
from src.service.utils.decorators import retry_enqueue
import asyncio

if TYPE_CHECKING:
    from src.service.extraction.service import ExtractionService
    from src.service.embedding.service import EmbeddingService
    from src.service.analytics.service import AnalyticsService
    from src.service.story.service import StoryService
    from src.service.chat.agent import ChatDeps

class ChapterWriteLocks:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    def get(self, chapter_id: str) -> asyncio.Lock:
        return self._locks.setdefault(chapter_id, asyncio.Lock())


class ChapterService:
    REEXTRACTION_THRESHOLD = 0.95

    def __init__(
        self,
        story_repo: StoryRepository,
        chapter_repo: ChapterRepository,
        scene_repo: SceneRepository,
        analytics_repo: AnalyticsRepository,
        provider: AIProvider,
        redis: aioredis.Redis,
    ):
        self._story_repo = story_repo
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo
        self._analytics_repo = analytics_repo
        self._provider = provider
        self._cache = redis
        self._locks = ChapterWriteLocks()

    # ─── reads ─────────────────────────────────────────────────────────────
    @cached_property
    def extraction_service(self) -> "ExtractionService":
        from src.service.extraction.service import ExtractionService

        return ExtractionService(self._provider, self._chapter_repo, self._scene_repo)

    @cached_property
    def embedding_service(self) -> "EmbeddingService":
        from src.service.embedding.service import EmbeddingService

        return EmbeddingService(self._scene_repo, self._provider)

    @cached_property
    def analytics_service(self) -> "AnalyticsService":
        from src.service.analytics.service import AnalyticsService

        return AnalyticsService(
            analytics_repo=self._analytics_repo,
            story_repo=self._story_repo,
            chapter_repo=self._chapter_repo,
            scene_repo=self._scene_repo,
            provider=self._provider,
            redis=self._cache
        )

    @cached_property
    def agent(self) -> Agent[ChatDeps, str]:
        from src.service.chat.agent import build_agent
        return build_agent(config.ai.default_model, system_prompt=COMMENTS_PLANNER_PROMPT)

    @cached_property
    def story_service(self) -> "StoryService":
        from src.service.story.service import StoryService

        return StoryService(
            story_repo=self._story_repo,
            chapter_repo=self._chapter_repo,
            scene_repo=self._scene_repo,
            provider=self._provider,
            search_config=config.search,
            redis=self._cache
        )

    @lru_cache
    def get_agent_chat_deps(
        self, user_id: str, story_id: str, story_status: StoryStatus
    ) -> "ChatDeps":
        from src.service.chat.agent import ChatDeps
        return ChatDeps(
            user_id=user_id,
            story_id=story_id,
            story_status=story_status,
            chapter_service=self,
            analytics_service=self.analytics_service,
            story_service=self.story_service
        )

    @handle_service_errors
    async def get_chapter_with_navigation(
        self,
        chapter_id: str,
        user_id: str,
        as_html: bool = True,
    ) -> ChapterContentResponse:
        triple = await self._chapter_repo.get_with_story_title(chapter_id, user_id)
        if triple is None:
            raise NotFoundError(
                "We couldn't find this chapter. It may have been deleted."
            )
        chapter, story_title, chapter_number = triple
        return ChapterContentResponse.from_chapter(
            chapter,
            content=chapter.content
            if as_html
            else get_preview_content(chapter.content or ""),
            story_title=story_title,
            chapter_number=chapter_number,
        )

    @handle_service_errors
    async def get_story_chapters(
        self,
        story_id: str,
        user_id: str,
    ) -> ChapterListResponse:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError(
                "We couldn't find this story. It may have been deleted."
            )

        results = await self._chapter_repo.list_by_story(story_id, user_id)
        if not story.path_array or not results:
            return ChapterListResponse.from_story(story, [])

        chapters = [result[0] for result in results]
        lookup = {c.id: c for c in chapters}

        items = []
        for i, cid in enumerate(story.path_array):
            if cid in lookup:
                row = lookup[cid]
                item = ChapterListItem(
                    story_id=row.story_id,
                    chapter_id=row.id,
                    chapter_number=i + 1,
                    word_count=row.word_count,
                    story_title=story.title,
                    chapter_title=row.title,
                    published=row.published,
                    updated_at=row.updated_at,
                )
                items.append(item)

        return ChapterListResponse.from_story(story, items)

    # ─── writes (transactional) ────────────────────────────────────────────
    @handle_service_errors
    async def _invalidate_chapter_analysis(
        self,
        chapter_id: str,
        story_id: str,
        user_id: str
    ) -> None:
        await self._cache.delete(
            f"chapter:baseline:{chapter_id}",
            f"chapter:extraction-pending:{chapter_id}",
            f"chapter:editorial_plan:{user_id}:{chapter_id}",
            f"summary:{chapter_id}:{user_id}",
            f"chapter:comments:{chapter_id}",
            f"pulse:{story_id}:{user_id}",
            f"plot_threads:{story_id}:{user_id}",
            f"act_segmentation:{story_id}:{user_id}",
            f"contradictions:{story_id}:{user_id}",
            f"entities:{story_id}:{user_id}",
            f"suggestion:character:context-v2:{story_id}:{user_id}",
            f"suggestion:plot:context-v2:{story_id}:{user_id}",
            f"suggestion:structure:context-v2:{story_id}:{user_id}",
            f"suggestion:world:context-v2:{story_id}:{user_id}"
        )

    @handle_service_errors
    async def _on_chapter_reorder(
        self,
        story_id: str,
        user_id: str,
        from_pos: int,
        to_pos: int
    ) -> None:
         story = await self._story_repo.get(story_id, user_id)

         if story is None:
            raise NotFoundError("Story not found")

         if story.path_array is None:
            return

         await self._cache.delete(
            f"pulse:{story_id}:{user_id}",
            f"plot_threads:{story_id}:{user_id}",
            f"act_segmentation:{story_id}:{user_id}",
            f"contradictions:{story_id}:{user_id}",
            f"entities:{story_id}:{user_id}",
            f"suggestion:character:context-v2:{story_id}:{user_id}",
            f"suggestion:plot:context-v2:{story_id}:{user_id}",
            f"suggestion:structure:context-v2:{story_id}:{user_id}",
            f"suggestion:world:context-v2:{story_id}:{user_id}"
         )

         start = min(from_pos, to_pos)
         affected_chapter_ids = story.path_array[start:]
         affected_chapters = await self._chapter_repo.list_by_ids(affected_chapter_ids)

         for chapter in affected_chapters:
              if not chapter.published:
                  continue

              await self._cache.delete(
                   f"summary:{chapter.id}:{user_id}",
                   f"chapter:editorial_plan:{user_id}:{chapter.id}",
                   f"chapter:comments:{chapter.id}"
               )

              pending_key = f"chapter:chapter-reanalysis-pending:{chapter.id}"
              claimed = await self._cache.set(
                  pending_key,
                  "1",
                  nx=True,
                  ex=1800,
              )

              if claimed:
                try:
                    await queue.enqueue(
                        "chapter_reanalysis_job",
                        story_id=story_id,
                        user_id=user_id,
                        chapter_id=chapter.id,
                        timeout=900,
                    )
                except Exception:
                    await self._cache.delete(pending_key)
                    raise

         story_pending_key = f"story:reanalysis-pending:{story.id}"
         claimed = await self._cache.set(
            story_pending_key,
            "1",
            nx=True,
            ex=1800,
         )

         if claimed:
            try:
                await queue.enqueue(
                    "story_reanalysis_job",
                    story_id=story_id,
                    user_id=user_id,
                    story_title=story.title,
                    timeout=900
                )
            except Exception:
                await self._cache.delete(story_pending_key)
                raise

    @handle_service_errors
    async def create_chapter(
        self,
        story_id: str,
        user_id: str,
        data: CreateChapterRequest,
    ) -> ChapterContentResponse:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError(
                "We couldn't find this story. It may have been deleted."
            )

        try:
            async with self._chapter_repo.pool.acquire() as conn:
                async with conn.transaction():
                    chapter = await self._chapter_repo.create(
                        story_id=story_id,
                        user_id=user_id,
                        title=data.title,
                        content="",
                        word_count=0,
                        executor=conn,
                    )
                    await self._handle_chapter_creation(
                        story_id,
                        chapter.id,
                        conn=conn,
                    )
        except (NotFoundError, ValidationError, InternalError):
            raise
        except Exception as e:
            logger.error(
                "chapter.create_failed",
                story_id=story_id,
                user_id=user_id,
                error=str(e),
            )
            raise InternalError(
                "Something went wrong while creating your chapter. Please try again."
            )

        logger.info(
            "chapter.create.done",
            story_id=story_id,
            chapter_id=chapter.id,
            user_id=user_id,
        )
        return await self.get_chapter_with_navigation(
            chapter.id,
            user_id,
            as_html=True,
        )

    @retry_enqueue
    async def _enqueue_extraction_job(
        self,
        *,
        chapter_id: str,
        story_id: str,
        user_id: str,
        content: str | None,
    ) -> None:
        await queue.enqueue(
            "scene_and_embedding_job",
            story_id=story_id,
            user_id=user_id,
            chapter_id=chapter_id,
            content=content,
            timeout=900,
        )

    @handle_service_errors
    async def queue_extraction_job(
        self,
        chapter_id: str,
        story_id: str,
        user_id: str,
        content: str | None = None,
    ) -> None:
        pending_key = f"chapter:extraction-pending:{chapter_id}"

        claimed = await self._cache.set(
            pending_key,
            "1",
            nx=True,
            ex=1800,
        )

        if not claimed:
            return

        try:
            await self._cache.delete(
                f"chapter:editorial_plan:{user_id}:{chapter_id}"
            )
            await self._enqueue_extraction_job(
                chapter_id=chapter_id,
                story_id=story_id,
                user_id=user_id,
                content=content,
            )
        except Exception:
            await self._cache.delete(pending_key)
            raise

    @handle_service_errors
    async def update_chapter(
        self,
        chapter_id: str,
        user_id: str,
        data: UpdateChapterRequest,
    ) -> ChapterContentResponse:

        triple = await self._chapter_repo.get_with_story_title(
            chapter_id,
            user_id,
        )
        if triple is None:
            raise NotFoundError(
                "We couldn't find this chapter. It may have been deleted."
            )

        chapter, story_title, chapter_number = triple
        fields = data.model_dump(exclude_unset=True, exclude={"expected_revision"})
        plain_text: str | None = None

        if "content" in fields:
            fields["word_count"] = get_word_count(fields["content"])
            plain_text = html_to_plain_text(fields["content"])

        async with self._chapter_repo.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                    chapter_id,
                )

                current = await self._chapter_repo.get(
                    chapter_id,
                    user_id,
                    executor=conn,
                )
                if current is None:
                    raise NotFoundError(
                        "We couldn't find this chapter. It may have been deleted."
                    )

                if (
                    data.expected_revision is not None
                    and current.updated_at != data.expected_revision
                ):
                    raise ConflictError(
                        "This chapter changed since you opened it. Your edit was not saved."
                    )

                chapter = current
                updated = await self._chapter_repo.update(
                    chapter_id=chapter_id,
                    user_id=user_id,
                    fields=fields,
                    executor=conn,
                )

        if updated is None:
            raise NotFoundError(
                "We couldn't find this chapter. It may have been deleted."
            )

        was_published = chapter.published
        is_published = updated.published
        became_published = not was_published and is_published
        became_draft = was_published and not is_published
        remained_published = was_published and is_published

        analysis_content = (
            plain_text
            if plain_text is not None
            else html_to_plain_text(updated.content or "")
        )

        try:
            if became_published and updated.word_count >= 1000:
                await self.queue_extraction_job(
                    chapter_id,
                    chapter.story_id,
                    chapter.user_id,
                    analysis_content
                )

            if became_draft:
                await self._invalidate_chapter_analysis(
                    chapter_id,
                    chapter.story_id,
                    chapter.user_id
                )

            if plain_text is not None and remained_published and updated.content:
                baseline_key = f"chapter:baseline:{chapter_id}"
                baseline = await self._cache.get(baseline_key)

                if baseline is None:
                    should_extract = updated.word_count >= 1000
                else:
                    should_extract = (
                        get_similarity_ratio(
                            baseline.decode() if isinstance(baseline, bytes) else baseline,
                            plain_text
                        ) < self.REEXTRACTION_THRESHOLD
                    )

                if should_extract:
                    await self.queue_extraction_job(
                        chapter_id,
                        chapter.story_id,
                        chapter.user_id,
                        analysis_content
                    )
        except Exception as e:
            logger.exception(
                "chapter.update_side_effect_failed",
                chapter_id=chapter_id,
                user_id=user_id,
                story_id=chapter.story_id,
                became_published=became_published,
                became_draft=became_draft,
                content_changed=plain_text is not None,
                error=str(e),
            )

        logger.info(
            "chapter.update.done",
            chapter_id=chapter_id,
            user_id=user_id,
            fields=list(fields.keys()),
        )

        return ChapterContentResponse.from_chapter(
            updated,
            story_title=story_title,
            chapter_number=chapter_number,
        )

    @handle_service_errors
    async def delete_chapter(
        self,
        chapter_id: str,
        user_id: str,
    ) -> dict:
        async with self._chapter_repo.pool.acquire() as conn:
            async with conn.transaction():
                story_id = await self._chapter_repo.delete(
                    chapter_id=chapter_id,
                    user_id=user_id,
                    executor=conn,
                )
                if story_id is None:
                    raise NotFoundError(
                        "We couldn't find this chapter. It may have been deleted."
                    )
                await self._handle_chapter_deletion(
                    story_id,
                    chapter_id,
                    conn=conn,
                )

        await self._invalidate_chapter_analysis(chapter_id, story_id, user_id)

        logger.info(
            "chapter.delete.done",
            chapter_id=chapter_id,
            user_id=user_id,
            story_id=story_id,
        )
        return {"message": "Chapter was successfully deleted"}

    @handle_service_errors
    async def reorder_chapters(
        self,
        story_id: str,
        user_id: str,
        data: ReorderChapterRequest,
    ) -> dict:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError(
                "We couldn't find this story. It may have been deleted."
            )

        if not story.path_array:
            raise ValidationError(message="This story has no chapters to reorder.")

        max_pos = len(story.path_array) - 1
        if not (0 <= data.from_pos <= max_pos):
            raise ValidationError(
                message=f"Invalid chapter position. Must be between 0 and {max_pos}.",
            )
        if not (0 <= data.to_pos <= max_pos):
            raise ValidationError(
                message=f"Invalid target position. Must be between 0 and {max_pos}.",
            )
        if data.from_pos == data.to_pos:
            return {"message": "No reordering needed"}

        try:
            async with self._chapter_repo.pool.acquire() as conn:
                async with conn.transaction():
                    await self._handle_chapter_reordering(
                        story_id,
                        data.from_pos,
                        data.to_pos,
                        conn=conn,
                    )
        except Exception as e:
            logger.error(
                "chapter.reorder_failed",
                story_id=story_id,
                user_id=user_id,
                phase="canonical",
                error=str(e),
            )
            raise InternalError(
                "Something went wrong while reordering your chapters. Please try again."
            )

        try:
            await self._on_chapter_reorder(
                story_id,
                user_id,
                data.from_pos,
                data.to_pos,
            )
        except Exception as e:
            logger.exception(
                "chapter.reorder_side_effect_failed",
                story_id=story_id,
                user_id=user_id,
                from_pos=data.from_pos,
                to_pos=data.to_pos,
                error=str(e),
            )

        logger.info(
            "chapter.reorder.done",
            story_id=story_id,
            user_id=user_id,
            from_pos=data.from_pos,
            to_pos=data.to_pos,
        )
        return {"message": "Chapters reordered successfully"}

    # ─── path-array & pointer primitives (private) ─────────────────────────

    async def _append_chapter_to_path_end(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> list[str]:
        path = await self._story_repo.append_chapter_to_path(
            story_id,
            chapter_id,
            executor=conn,
        )
        if path is None:
            raise ValueError(f"Story {story_id} not found")
        return path

    async def _remove_chapter_from_path(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> list[str] | None:
        return await self._story_repo.remove_chapter_from_path(
            story_id,
            chapter_id,
            executor=conn,
        )

    async def _reorder_chapter_path(
        self,
        story_id: str,
        from_pos: int,
        to_pos: int,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> list[str] | None:
        return await self._story_repo.reorder_chapter_path(
            story_id,
            from_pos,
            to_pos,
            executor=conn,
        )

    async def _sync_all_chapter_pointers(
        self,
        story_id: str,
        path: list[str] | None = None,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        if path is None:
            path = await self._story_repo.get_path_array(story_id, executor=conn)
        if path is None:
            return
        await self._chapter_repo.sync_pointers(story_id, path, executor=conn)

    async def _update_story_timestamp(
        self,
        story_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        await self._story_repo.touch(story_id, executor=conn)

    # ─── orchestration (private) ───────────────────────────────────────────

    async def _handle_chapter_creation(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._append_chapter_to_path_end(story_id, chapter_id, conn=conn)
        await self._sync_all_chapter_pointers(story_id, path, conn=conn)
        logger.info(
            "chapter.path_created",
            chapter_id=chapter_id,
            story_id=story_id,
        )

    async def _handle_chapter_deletion(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._remove_chapter_from_path(story_id, chapter_id, conn=conn)
        await self._sync_all_chapter_pointers(story_id, path, conn=conn)
        logger.info(
            "chapter.path_deleted",
            chapter_id=chapter_id,
            story_id=story_id,
        )

    async def _handle_chapter_reordering(
        self,
        story_id: str,
        from_pos: int,
        to_pos: int,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._reorder_chapter_path(story_id, from_pos, to_pos, conn=conn)
        await self._sync_all_chapter_pointers(story_id, path, conn=conn)
        logger.info(
            "chapter.path_reordered",
            story_id=story_id,
            from_pos=from_pos,
            to_pos=to_pos,
        )

    def _format_scenes(self, scenes: List[SceneRow]) -> str:
        formatted_scenes = []

        for i, scene in enumerate(scenes):
            header = f"""\
            SCENE - {i + 1}
            TITLE: {scene.title}
            TENSION: {scene.tension} PACING: {scene.pacing}
            """

            body = f"""\
            DESCRIPTION:
            {scene.description}
            MENTIONED ENTITIES:
            {", ".join(scene.mentioned_entities)}
            TAGS:
            {", ".join(scene.tags)}
            OPEN QUESTIONS RAISED:
            {chr(10).join(f" - {q}" for q in scene.questions_raised)}
            """

            formatted_scenes.append("\n".join([header, body]))

        return "\n".join(formatted_scenes)

    @handle_service_errors
    async def get_story_context(
        self, user_id: str, story_id: str, chapter_id: Optional[str] = None
    ) -> str:
        scenes = await self._scene_repo.list_by_story(
            story_id=story_id, user_id=user_id, chapter_id=chapter_id
        )

        path_array = await self._story_repo.get_path_array(story_id)

        if path_array is None:
            raise NotFoundError("Story not found")

        scenes = sorted(scenes, key=lambda scene: path_array.index(scene.chapter_id))
        story_ctx = self._format_scenes(scenes)
        return story_ctx

    @handle_service_errors
    async def summarize_chapter(
        self, chapter_id: str, user_id: str, ignore_cache: bool = False
    ) -> ChapterSummaryResponse:
        chapter_to_summarize = await self._chapter_repo.get(chapter_id, user_id)

        if chapter_to_summarize is None:
            raise NotFoundError("Chapter not found")

        if not chapter_to_summarize.published:
            raise ValidationError(
                message="Publish this chapter before generating manuscript analysis."
            )

        if get_word_count(chapter_to_summarize.content or "") <= 500:
            return ChapterSummaryResponse(summary="")

        cache_key = f"summary:{chapter_id}:{user_id}"

        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return ChapterSummaryResponse.model_validate_json(raw_data)

        ctx = await self.get_story_context(
            user_id=user_id,
            story_id=chapter_to_summarize.story_id,
            chapter_id=chapter_to_summarize.prev_chapter_id,
        )

        summary = await self._provider.generate(
            system_prompt=SUMMARIZATION_PROMPT,
            text=f"""\
            <story_context_so_far>
            {ctx}
            </story_context_so_far>

            <chapter_text>
            {html_to_plain_text(chapter_to_summarize.content or "")}
            </chapter_text>
            """,
            max_tokens=config.ai.summarization_max_tokens,
        )

        logger.info("chapter.summary", chapter_id=chapter_id, user_id=user_id)
        response = ChapterSummaryResponse(summary=summary)

        await self._cache.set(
            cache_key, response.model_dump_json(), ex=timedelta(minutes=30)
        )
        return response

    @handle_service_errors
    async def generate_editorial_plan(
        self,
        chapter_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> str:
        triple = await self._chapter_repo.get_with_story_title(chapter_id, user_id)

        if triple is None:
            raise NotFoundError("Chapter not found")

        chapter, story_title, chapter_number = triple

        if not chapter.published:
            raise ValidationError(
                message="Publish this chapter before generating manuscript analysis."
            )

        story = await self._story_repo.get(chapter.story_id, user_id)
        if story is None:
            raise NotFoundError("Story not found")

        if not ignore_cache:
            if plan := (await self._cache.get(f"chapter:editorial_plan:{user_id}:{chapter_id}")):
                return plan.decode() if isinstance(plan, bytes) else plan

        result = await self.agent.run(
            user_prompt=textwrap.dedent(
                f"""\
                <inputs>
                    <target_chapter>
                        # Chapter {chapter_number} of {story_title}

                        {html_to_plain_text(chapter.content or "")}
                    </target_chapter>
                </inputs>
                """
            ),
            deps=self.get_agent_chat_deps(user_id, chapter.story_id, story.status)
        )

        plan = result.output
        await self._cache.set(f"chapter:editorial_plan:{user_id}:{chapter_id}", plan)
        return plan

    @handle_service_errors
    async def generate_comments(
        self,
        user_id: str,
        chapter_id: str,
        ignore_cache: bool = False
    ) -> CommentExtractionResponse:
        triple = await self._chapter_repo.get_with_story_title(chapter_id, user_id)

        if triple is None:
            raise NotFoundError("Chapter not found")

        chapter, story_title, chapter_number = triple

        if not chapter.published:
            raise ValidationError(
                message="Publish this chapter before generating manuscript analysis."
            )

        if not ignore_cache:
            if raw_data := (await self._cache.get(f"chapter:comments:{chapter_id}")):
                return CommentExtractionResponse.model_validate_json(raw_data)

        plan = await self.generate_editorial_plan(chapter_id, user_id)

        extraction = await self._provider.extract(
            system_prompt=COMMENTS_EXTRACTION_PROMPT,
            text=textwrap.dedent(
                f"""\
                <inputs>
                    <review_plan>
                        {plan}
                    </review_plan>
                    <target_chapter>
                        # Chapter {chapter_number} of {story_title}

                        {html_to_plain_text(chapter.content or "")}
                    </target_chapter>
                </inputs>
                """
            ),
            max_tokens=config.ai.comments_max_tokens,
            schema=CommentExtraction
        )

        response = CommentExtractionResponse(
            story_id=chapter.story_id,
            story_title=story_title,
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            generated_at=datetime.now(tz=tz.utc),
            extraction=extraction
        )

        await self._cache.set(f"chapter:comments:{chapter_id}", response.model_dump_json())
        return response

    @handle_service_errors
    async def get_comments(
        self,
        user_id: str,
        chapter_id: str
    ) -> CommentExtractionResponse:
        triple = await self._chapter_repo.get_with_story_title(chapter_id, user_id)

        if triple is None:
            raise NotFoundError("Chapter not found")

        chapter, story_title, chapter_number = triple

        if not chapter.published:
            return CommentExtractionResponse(
                story_id=chapter.story_id,
                story_title=story_title,
                chapter_id=chapter_id,
                chapter_number=chapter_number,
                generated_at=datetime.now(tz=tz.utc),
                extraction=CommentExtraction(comments=[]),
            )

        raw_data = await self._cache.get(f"chapter:comments:{chapter_id}")

        if raw_data is None:
            return CommentExtractionResponse(
                story_id=chapter.story_id,
                story_title=story_title,
                chapter_id=chapter_id,
                chapter_number=chapter_number,
                generated_at=datetime.now(tz=tz.utc),
                extraction=CommentExtraction(
                    comments=[]
                )
            )

        return CommentExtractionResponse.model_validate_json(raw_data)
