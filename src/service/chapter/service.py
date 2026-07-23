from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, List, Optional

import asyncpg
from loguru import logger

from src.data.repositories import (
    StoryRepository,
    ChapterRepository,
    SceneRepository,
)
from src.data.schemas import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse,
)
from src.data.schemas.chapter import ChapterSummaryResponse
from src.data.schemas.scene import SceneRow
from src.infrastructure.config import config
from src.infrastructure.ai.prompts import SUMMARIZATION_PROMPT
from src.infrastructure.ai.providers.protocol import AIProvider
from src.service.exceptions import NotFoundError, ValidationError, InternalError
from src.service.extraction import scenes_are_stale
from src.service.utils.decorators import handle_service_errors
from functools import cached_property
from src.infrastructure.redis.queue import queue
from datetime import timedelta
import redis.asyncio as aioredis
from src.shared.utils.html import (
    get_html_similarity_ratio,
    get_preview_content,
    get_word_count,
    html_to_plain_text,
)

if TYPE_CHECKING:
    from src.service.extraction.service import ExtractionService
    from src.service.embedding.service import EmbeddingService

class ChapterService:

    REEXTRACTION_THRESHOLD = 0.95

    def __init__(
        self,
        story_repo: StoryRepository,
        chapter_repo: ChapterRepository,
        scene_repo: SceneRepository,
        provider: AIProvider,
        redis: aioredis.Redis
    ):
        self._story_repo = story_repo
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo
        self._provider = provider
        self._cache = redis
        self._background_tasks: set[asyncio.Task] = set()

    # ─── reads ─────────────────────────────────────────────────────────────
    @cached_property
    def extraction_service(self) -> "ExtractionService":
        from src.service.extraction.service import ExtractionService
        return ExtractionService(self._provider, self._chapter_repo, self._scene_repo)
    
    @cached_property
    def embedding_service(self) -> "EmbeddingService":
        from src.service.embedding.service import EmbeddingService
        return EmbeddingService(self._scene_repo, self._provider)
        

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
            content=chapter.content if as_html else get_preview_content(chapter.content),
            story_title=story_title,
            chapter_number=chapter_number
        )

    @handle_service_errors
    async def get_story_chapters(
        self,
        story_id: str,
        user_id: str,
    ) -> ChapterListResponse:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        results = await self._chapter_repo.list_by_story(story_id, user_id)
        if not story.path_array or not results:
            return ChapterListResponse.from_story(story, [])
        
        chapters = [result[0] for result in results]

        lookup = {c.id: c for c in chapters}
        
        # Explicit mapping loop: reading direct properties from the database object
        items = []
        for i, cid in enumerate(story.path_array):
            if cid in lookup:
                row = lookup[cid]
                item = ChapterListItem(
                    story_id=row.story_id,
                    chapter_id=row.id,  # Manually mapping 'id' to 'chapter_id'
                    chapter_number=i+1,
                    word_count=row.word_count,
                    story_title=story.title,
                    chapter_title=row.title,
                    published=row.published,
                    updated_at=row.updated_at
                )
                items.append(item)

        return ChapterListResponse.from_story(story, items)


    # ─── writes (transactional) ────────────────────────────────────────────

    @handle_service_errors
    async def create_chapter(
        self,
        story_id: str,
        user_id: str,
        data: CreateChapterRequest,
    ) -> ChapterContentResponse:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")


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
                        story_id, chapter.id, conn=conn,
                    )
        except (NotFoundError, ValidationError, InternalError):
            raise
        except Exception as e:
            logger.error(
                "chapter.create_failed",
                story_id=story_id, user_id=user_id, error=str(e),
            )
            raise InternalError(
                "Something went wrong while creating your chapter. Please try again."
            )

        logger.info(
            "chapter.create.done",
            story_id=story_id, chapter_id=chapter.id, user_id=user_id,
        )
        return await self.get_chapter_with_navigation(
            chapter.id, user_id, as_html=True,
        )

    @handle_service_errors
    async def update_chapter(
        self,
        chapter_id: str,
        user_id: str,
        data: UpdateChapterRequest,
    ) -> ChapterContentResponse:
        triple = await self._chapter_repo.get_with_story_title(chapter_id, user_id)
        if triple is None:
            raise NotFoundError(
                "We couldn't find this chapter. It may have been deleted."
            )
        chapter, story_title, chapter_number = triple

        fields = data.model_dump(exclude_unset=True)
        if "content" in fields:
            fields["word_count"] = get_word_count(fields["content"])

            # If existing scenes' quotes no longer line up with the new content,
            # flag the chapter for re-extraction. Avoids churn on trivial edits
            # (typos, formatting) where every quote still matches verbatim.
            existing_scenes = await self._scene_repo.list_by_chapter(chapter_id)
            if existing_scenes:
                new_plain_text = html_to_plain_text(fields["content"])
                if scenes_are_stale(existing_scenes, new_plain_text):
                    await self._scene_repo.mark_chapter_stale(chapter_id)

        async with self._chapter_repo.pool.acquire() as conn:
            async with conn.transaction():
                updated = await self._chapter_repo.update(
                    chapter_id=chapter_id,
                    user_id=user_id,
                    fields=fields,
                    executor=conn,
                )

        if updated is None:
            # disappeared between the read above and the update — treat as gone
            raise NotFoundError(
                "We couldn't find this chapter. It may have been deleted."
            )
    
        
        if  (
            "content" in fields 
             and chapter.content
             and updated.content
             and get_html_similarity_ratio(chapter.content, updated.content) < self.REEXTRACTION_THRESHOLD
        ): 
            await queue.enqueue(
                "scene_and_embedding_job",
                chapter_id=chapter_id,
                timeout=900
            )

        logger.info(
            "chapter.update.done",
            chapter_id=chapter_id, user_id=user_id, fields=list(fields.keys()),
        )
        return ChapterContentResponse.from_chapter(updated, story_title=story_title, chapter_number=chapter_number)

    @handle_service_errors
    async def delete_chapter(
        self,
        chapter_id: str,
        user_id: str,
    ) -> dict:
        async with self._chapter_repo.pool.acquire() as conn:
            async with conn.transaction():
                story_id = await self._chapter_repo.delete(
                    chapter_id=chapter_id, user_id=user_id, executor=conn,
                )
                if story_id is None:
                    raise NotFoundError(
                        "We couldn't find this chapter. It may have been deleted."
                    )
                await self._handle_chapter_deletion(
                    story_id, chapter_id, conn=conn,
                )

        logger.info(
            "chapter.delete.done",
            chapter_id=chapter_id, user_id=user_id, story_id=story_id,
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
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

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
                        story_id, data.from_pos, data.to_pos, conn=conn,
                    )
        except Exception as e:
            logger.error(
                "chapter.reorder_failed",
                story_id=story_id, user_id=user_id, error=str(e),
            )
            raise InternalError(
                "Something went wrong while reordering your chapters. Please try again."
            )

        logger.info(
            "chapter.reorder.done",
            story_id=story_id, user_id=user_id,
            from_pos=data.from_pos, to_pos=data.to_pos,
        )
        return {"message": "Chapters reordered successfully"}

    # ─── path-array & pointer primitives (private) ─────────────────────────
    #
    # Operate purely on `path_array` (the ordering source of truth) and the
    # `prev_chapter_id`/`next_chapter_id` pointers (derived from it). All take
    # an optional `conn` so the public method can compose them into a single
    # transaction.

    async def _append_chapter_to_path_end(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._story_repo.get_path_array(story_id, executor=conn)
        if path is None:
            raise ValueError(f"Story {story_id} not found")

        if chapter_id in path:
            return

        await self._story_repo.set_path_array(
            story_id, [*path, chapter_id], executor=conn,
        )

    async def _remove_chapter_from_path(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._story_repo.get_path_array(story_id, executor=conn)
        if not path or chapter_id not in path:
            return

        await self._story_repo.set_path_array(
            story_id, [c for c in path if c != chapter_id], executor=conn,
        )

    async def _reorder_chapter_path(
        self,
        story_id: str,
        from_pos: int,
        to_pos: int,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        path = await self._story_repo.get_path_array(story_id, executor=conn)
        if not path:
            return

        last = len(path) - 1
        if not (0 <= from_pos <= last) or not (0 <= to_pos <= last):
            return
        if from_pos == to_pos:
            return

        new_path = list(path)
        new_path.insert(to_pos, new_path.pop(from_pos))
        await self._story_repo.set_path_array(story_id, new_path, executor=conn)

    async def _sync_all_chapter_pointers(
        self,
        story_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
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
        await self._append_chapter_to_path_end(story_id, chapter_id, conn=conn)
        await self._sync_all_chapter_pointers(story_id, conn=conn)
        await self._update_story_timestamp(story_id, conn=conn)
        logger.info(
            "chapter.path_created", chapter_id=chapter_id, story_id=story_id,
        )

    async def _handle_chapter_deletion(
        self,
        story_id: str,
        chapter_id: str,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        await self._remove_chapter_from_path(story_id, chapter_id, conn=conn)
        await self._sync_all_chapter_pointers(story_id, conn=conn)
        await self._update_story_timestamp(story_id, conn=conn)
        logger.info(
            "chapter.path_deleted", chapter_id=chapter_id, story_id=story_id,
        )

    async def _handle_chapter_reordering(
        self,
        story_id: str,
        from_pos: int,
        to_pos: int,
        *,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        await self._reorder_chapter_path(story_id, from_pos, to_pos, conn=conn)
        await self._sync_all_chapter_pointers(story_id, conn=conn)
        await self._update_story_timestamp(story_id, conn=conn)
        logger.info(
            "chapter.path_reordered",
            story_id=story_id, from_pos=from_pos, to_pos=to_pos,
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
            {"\n".join(f" - {q}" for q in scene.questions_raised)}
            """

            formatted_scenes.append("\n".join([header, body]))

        return "\n".join(formatted_scenes)
    
    @handle_service_errors
    async def get_story_context(
        self, user_id: str, story_id: str, chapter_id: Optional[str] = None
    ) -> str:
        
        scenes = await self._scene_repo.list_by_story(
            story_id=story_id, 
            user_id=user_id, 
            chapter_id=chapter_id
        )
            
        story_ctx = self._format_scenes(scenes)

        return story_ctx

    @handle_service_errors
    async def summarize_chapter(
        self,
        chapter_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> ChapterSummaryResponse:
        
        chapter_to_summarize = await self._chapter_repo.get(chapter_id, user_id)

        if chapter_to_summarize is None:
            raise NotFoundError("Chapter not found")
        
        if get_word_count(chapter_to_summarize.content) <= 500:
            return ChapterSummaryResponse(summary="")
        
        cache_key = f"summary:{chapter_id}:{user_id}"

        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return ChapterSummaryResponse.model_validate_json(raw_data)
        
        ctx = await self.get_story_context(
            user_id=user_id,
            story_id=chapter_to_summarize.story_id,
            chapter_id=chapter_to_summarize.prev_chapter_id
        )

        summary = await self._provider.generate(
            system_prompt=SUMMARIZATION_PROMPT,
            text=f"""\
            <story_context_so_far>
            {ctx}
            </story_context_so_far>

            <chapter_text>
            {html_to_plain_text(chapter_to_summarize.content)}
            </chapter_text>
            """,
            max_tokens=config.ai.summarization_max_tokens
        )

        logger.info("chapter.summary", chapter_id=chapter_id, user_id=user_id)

        response =  ChapterSummaryResponse(summary=summary)

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(minutes=30))

        return response


