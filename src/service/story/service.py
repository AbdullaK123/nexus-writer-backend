from typing import List, Literal

from loguru import logger

from src.data.repositories import StoryRepository, ChapterRepository, SceneRepository
from src.data.schemas.chapter import ChapterListItem
from src.data.schemas.scene import (
    SceneSearchResponse,
    VocabularyItem,
    VocabularyListResponse,
)
from src.data.schemas.story import (
    CreateStoryRequest,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse,
)
from src.infrastructure.ai.providers.protocol import AIProvider
from src.infrastructure.config.settings import SearchConfig
from src.service.exceptions import NotFoundError, ConflictError
from src.service.utils.decorators import handle_service_errors


class StoryService:
    def __init__(
        self,
        story_repo: StoryRepository,
        chapter_repo: ChapterRepository,
        scene_repo: SceneRepository,
        provider: AIProvider,
        search_config: SearchConfig,
    ):
        self._story_repo = story_repo
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo
        self._provider = provider
        self._search_config = search_config

    @handle_service_errors
    async def create_story(
        self,
        user_id: str,
        story_info: CreateStoryRequest,
    ) -> dict:
        if await self._story_repo.exists_with_title(user_id, story_info.title):
            logger.warning(
                "story.create.conflict", user_id=user_id, title=story_info.title,
            )
            raise ConflictError(
                "You already have a story with this title. Please choose a different one."
            )

        await self._story_repo.create(user_id=user_id, title=story_info.title)
        logger.info("story.create.done", user_id=user_id, title=story_info.title)
        return {"message": "Story successfully created"}

    @handle_service_errors
    async def update_story(
        self,
        user_id: str,
        story_id: str,
        update_info: UpdateStoryRequest,
    ) -> dict:
        fields = update_info.model_dump(exclude_unset=True)

        updated = await self._story_repo.update(
            story_id=story_id, user_id=user_id, fields=fields,
        )
        if updated is None:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        logger.info(
            "story.update.done",
            user_id=user_id, story_id=story_id, fields=list(fields.keys()),
        )
        return {"message": "Story successfully updated"}

    @handle_service_errors
    async def delete_story(self, user_id: str, story_id: str) -> dict:
        deleted = await self._story_repo.delete(story_id=story_id, user_id=user_id)
        if not deleted:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        logger.info("story.delete.done", user_id=user_id, story_id=story_id)
        return {"message": "Story successfully deleted"}

    # ─── reads ─────────────────────────────────────────────────────────────

    @staticmethod
    def _order_chapters_by_path(
        chapters: list, path_array: list[str] | None,
    ) -> list:
        """Reorder a flat chapter list to match story.path_array. Falls back
        to newest-first when no path is set (matches the previous behaviour)."""
        if not path_array:
            return sorted(chapters, key=lambda c: c.created_at, reverse=True)

        lookup = {c.id: c for c in chapters}
        return [lookup[cid] for cid in path_array if cid in lookup]

    @handle_service_errors
    async def get_story_details(
        self,
        user_id: str,
        story_id: str,
    ) -> StoryDetailResponse:
        story = await self._story_repo.get(story_id, user_id)
        if story is None:
            raise NotFoundError("A story with that title does not exist")

        chapters = await self._chapter_repo.list_by_story(story_id, user_id)
        ordered = self._order_chapters_by_path(chapters, story.path_array)
        chapter_items = [ChapterListItem.model_validate(c) for c in ordered]

        return StoryDetailResponse.from_story(story, chapter_items)

    @handle_service_errors
    async def get_all_stories(self, user_id: str) -> StoryGridResponse:
        stories = await self._story_repo.list_for_user(user_id)
        if not stories:
            return StoryGridResponse(stories=[])

        all_chapters = await self._chapter_repo.list_by_story_ids(
            [s.id for s in stories],
        )

        by_story: dict[str, list] = {}
        for ch in all_chapters:
            by_story.setdefault(ch.story_id, []).append(ch)

        cards = [
            StoryCardResponse.from_story(s, by_story.get(s.id, [])) for s in stories
        ]
        return StoryGridResponse(stories=cards)
    
    @handle_service_errors
    async def search_story_scenes(
        self,
        user_id: str,
        story_id: str,
        query_text: str,
        k: int | None = None,
        candidate_pool: int | None = None,
        tension: Literal["low", "medium", "high"] | None = None,
        pacing: Literal["slow", "steady", "fast"] | None = None,
        tags: list[str] | None = None,
        mentioned_entities: list[str] | None = None,
        chapter_ids: list[str] | None = None,
    ) -> List[SceneSearchResponse]:

        query_text = query_text.strip()
        if not query_text:
            logger.info(
                "story.search.empty_query",
                user_id=user_id, story_id=story_id,
            )
            return []

        # Per-call overrides win; otherwise fall back to config so ops can
        # tune without a code change.
        k = k if k is not None else self._search_config.default_k
        candidate_pool = (
            candidate_pool
            if candidate_pool is not None
            else self._search_config.default_candidate_pool
        )

        logger.info(
            "story.search.start",
            user_id=user_id,
            story_id=story_id,
            query_len=len(query_text),
            k=k,
            candidate_pool=candidate_pool,
            tension=tension,
            pacing=pacing,
            tags=tags,
            mentioned_entities=mentioned_entities,
            chapter_ids=chapter_ids,
        )

        query_embedding = await self._provider.embed(query_text)

        search_results = await self._scene_repo.search_scenes(
            user_id=user_id,
            story_id=story_id,
            query_text=query_text,
            query_embedding=query_embedding,
            k=k,
            pacing=pacing,
            tension=tension,
            tags=tags,
            mentioned_entities=mentioned_entities,
            chapter_ids=chapter_ids,
            candidate_pool=candidate_pool,
        )

        logger.info(
            "story.search.done",
            user_id=user_id,
            story_id=story_id,
            query_len=len(query_text),
            results=len(search_results),
        )

        return [
            SceneSearchResponse.from_result(result)
            for result in search_results
        ]

    @handle_service_errors
    async def list_story_tags(
        self, user_id: str, story_id: str,
    ) -> VocabularyListResponse:
        """Return every distinct tag in this story's scenes with its count,
        sorted by frequency desc. Authorisation is row-level via user_id
        — a foreign story silently returns an empty list."""
        rows = await self._scene_repo.list_story_tags(
            user_id=user_id, story_id=story_id,
        )
        return VocabularyListResponse(
            items=[VocabularyItem(value=v, count=n) for v, n in rows],
        )

    @handle_service_errors
    async def list_story_entities(
        self, user_id: str, story_id: str,
    ) -> VocabularyListResponse:
        """Return every distinct mentioned entity in this story's scenes
        with its count, sorted by frequency desc. Same auth model as
        `list_story_tags`."""
        rows = await self._scene_repo.list_story_entities(
            user_id=user_id, story_id=story_id,
        )
        return VocabularyListResponse(
            items=[VocabularyItem(value=v, count=n) for v, n in rows],
        )

