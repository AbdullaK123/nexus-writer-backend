import asyncio
from typing import List, Literal, Optional

from loguru import logger

from src.data.repositories import StoryRepository, ChapterRepository, SceneRepository
from src.data.schemas.chapter import ChapterListItem, ChapterRow
from src.data.schemas.enums import StoryStatus
from src.data.schemas.extraction import INSUFFICIENT_CONTEXT, BookPulseResponse, PulseDimension
from src.data.schemas.scene import (
    SceneRow,
    SceneSearchResponse,
    SceneSearchResult,
    VocabularyItem,
    VocabularyListResponse,
)
from src.data.schemas.story import (
    CreateStoryRequest,
    StoryPathArrayResponse,
    StoryStatsResponse,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse,
)
from src.infrastructure.ai.prompts import CHARACTER_PULSE_PROMPT, PLOT_PULSE_PROMPT, STRUCTURE_PULSE_PROMPT, WORLD_PULSE_PROMPT
from src.infrastructure.ai.providers.protocol import AIProvider
from src.infrastructure.config.settings import SearchConfig
from src.service.exceptions import NotFoundError, ConflictError
from src.service.utils.decorators import handle_service_errors
from src.infrastructure.config import config


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

        results = await self._chapter_repo.list_by_story(story_id, user_id)

        results = sorted(results, key=lambda x: x[2])

        chapter_items = [
            ChapterListItem(
                story_id=c.story_id,
                chapter_id=c.id,
                chapter_number=chapter_number,
                word_count=c.word_count,
                story_title=story_title,
                chapter_title=c.title,
                published=c.published,
                updated_at=c.updated_at
            )
            for c, story_title, chapter_number in results
        ]

        return StoryDetailResponse.from_story(story, chapter_items)

    @handle_service_errors
    async def get_all_stories(self, user_id: str, status: Optional[StoryStatus] = None) -> StoryGridResponse:

        stories = await self._story_repo.list_for_user(user_id)
        if not stories:
            return StoryGridResponse(stories=[])
        
        if status:
            story_ids = [s.id for s in stories if s.status == status]
        else:
            story_ids = [s.id for s in stories]

        all_chapters = await self._chapter_repo.list_by_story_ids(
            story_ids
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
        pov: str | None = None,
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
        
        story_path_array = await self._story_repo.get_path_array(story_id)

        if story_path_array is None:
            raise NotFoundError("Story not found")

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

        search_results: List[SceneSearchResult] = await self._scene_repo.search_scenes(
            user_id=user_id,
            story_id=story_id,
            query_text=query_text,
            query_embedding=query_embedding,
            k=k,
            pacing=pacing,
            tension=tension,
            tags=tags,
            mentioned_entities=mentioned_entities,
            pov=pov,
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
            SceneSearchResponse(
                id=result.id,
                chapter_id=result.chapter_id,
                chapter_number=story_path_array.index(result.chapter_id) + 1,
                story_id=result.story_id,
                title=result.title,
                description=result.description,
                start_quote=result.start_quote,
                end_quote=result.end_quote,
                tension=result.tension,
                pacing=result.pacing,
                mentioned_entities=result.mentioned_entities,
                tags=result.tags,
                questions_raised=result.questions_raised,
                score=result.score,
                created_at=result.created_at,
                updated_at=result.updated_at,
                chapter_title=result.chapter_title
            )
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
    
    @handle_service_errors
    async def list_povs(
        self, user_id: str, story_id: str
    ) -> VocabularyListResponse:
        """Return every distinct pov in this story's scenes
        with its count, sorted by frequency desc. Same auth model as
        `list_story_tags`."""
        rows = await self._scene_repo.list_povs(
            user_id=user_id, story_id=story_id,
        )
        return VocabularyListResponse(
            items=[VocabularyItem(value=v, count=n) for v, n in rows],
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

        if len(scenes) < 3:
            return "NOT_ENOUGH_CONTEXT"
            
        story_ctx = self._format_scenes(scenes)

        return story_ctx
    
    @handle_service_errors
    async def get_pulse(
        self, user_id: str, story_id: str
    ) -> BookPulseResponse:
        
        # get story_context
        story_ctx = await self.get_story_context(user_id, story_id)

        if story_ctx == "NOT_ENOUGH_CONTEXT":
            return INSUFFICIENT_CONTEXT

        character_pulse_task = self._provider.extract(
            system_prompt=CHARACTER_PULSE_PROMPT,
            text=f"""\
            <story_context>
            {story_ctx}
            </story_context>
            """,
            max_tokens=config.ai.pulse_extraction_max_tokens,
            schema=PulseDimension
        )
        plot_pulse_task = self._provider.extract(
            system_prompt=PLOT_PULSE_PROMPT,
            text=f"""\
            <story_context>
            {story_ctx}
            </story_context>
            """,
            max_tokens=config.ai.pulse_extraction_max_tokens,
            schema=PulseDimension
        )
        structure_pulse_task = self._provider.extract(
            system_prompt=STRUCTURE_PULSE_PROMPT,
            text=f"""\
            <story_context>
            {story_ctx}
            </story_context>
            """,
            max_tokens=config.ai.pulse_extraction_max_tokens,
            schema=PulseDimension
        )
        world_pulse_task = self._provider.extract(
            system_prompt=WORLD_PULSE_PROMPT,
            text=f"""\
            <story_context>
            {story_ctx}
            </story_context>
            """,
            max_tokens=config.ai.pulse_extraction_max_tokens,
            schema=PulseDimension
        )

        # four parellel extractions
        character_result, plot_result, structure_result, world_result = \
            await asyncio.gather(
                character_pulse_task,
                plot_pulse_task,
                structure_pulse_task,
                world_pulse_task,
                return_exceptions=False
            )

        return BookPulseResponse(
            characters=character_result,
            plot=plot_result,
            structure=structure_result,
            world=world_result
        )
    
    @handle_service_errors
    async def get_path_array(
        self,
        story_id: str,
        user_id: str
    ) -> StoryPathArrayResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        path_array =  await self._story_repo.get_path_array(story_id)

        return StoryPathArrayResponse(path_array=path_array)
    
    @handle_service_errors
    async def get_story_stats(
        self,
        story_id: str,
        user_id: str
    ) -> StoryStatsResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        stats = await self._story_repo.get_stats(story_id, user_id)

        return StoryStatsResponse(
            total_words=stats.get("total_words", 0),
            total_chapters=stats.get("chapters_total", 0),
            total_scenes=stats.get("scenes_tracked", 0),
            streak_days=stats.get("streak_days", 0)
        )

