from functools import cached_property
import textwrap
from datetime import datetime, timezone as tz, timedelta
from typing import Literal, TYPE_CHECKING
import redis.asyncio as aioredis
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.scene import SceneRepository
from src.service.exceptions import NotFoundError, ServiceError
from src.data.repositories.analytics import AnalyticsRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.analytics import ActSegmentationExtraction, ActSegmentationResponse, AnalyticsSuggestionExtraction, ContradictionExtraction, ContradictionResponse, EntityLedgerExtraction, EntityLedgerResponse, PlotThreadsExtraction, AnalyticsSuggestionResponse, CastStatisticsResponse, CastStatisticsRow, CharacterStatisticsResponse, CharacterStatisticsRow, CoOccurenceStatisticsResponse, CoOccurenceStatisticsRow, PacingCurveRow, PlotThreadsResponse, SceneLengthDistributionResponse, SceneLengthDistributionRow, TensionAndPacingCurveResponse, TensionCurveRow
from src.infrastructure.ai.providers.protocol import AIProvider
from src.infrastructure.config.settings import config
from prettytable import PrettyTable
import asyncio
from src.infrastructure.ai.prompts import (
    CHARACTER_ANALYTICS_SUGGESTION_PROMPT,
    CONTRADICTION_EXTRACTION_PROMPT,
    PLOT_ANALYTICS_SUGGESTION_PROMPT,
    PLOT_THREADS_EXTRACTION_PROMPT,
    STRUCTURE_ANALYTICS_SUGGESTION_PROMPT,
    WORLD_ANALYTICS_SUGGESTION_PROMPT,
    PLOT_THREADS_EXTRACTION_PROMPT,
    ACT_SEGMENTATION_EXTRACTION_PROMPT,
    ENTITY_LEDGER_EXTRACTION_PROMPT
)

if TYPE_CHECKING:
    from src.service.story.service import StoryService

class AnalyticsService:

    prompt_map = {
        "character": CHARACTER_ANALYTICS_SUGGESTION_PROMPT,
        "plot": PLOT_ANALYTICS_SUGGESTION_PROMPT,
        "structure": STRUCTURE_ANALYTICS_SUGGESTION_PROMPT,
        "world": WORLD_ANALYTICS_SUGGESTION_PROMPT
    }
    prompt_template_map = {
        "character": textwrap.dedent(
        """\
        <inputs>
            <cast_statistics>
                {cast_statistics}
            </cast_statistics>
            <co_occurrence_statistics>
                {co_occurrence_statistics}
            </co_occurrence_statistics>
            <character_statistics>
                {character_statistics}
            </character_statistics>
        </inputs>
        """
        ),
        "plot": textwrap.dedent(
            """\
            <inputs>
                <plot_threads>
                    {plot_threads}
                </plot_threads>
                <act_segmentation>
                    {act_segmentation}
                </act_segmentation>
            </inputs>
            """
        ),
        "structure": textwrap.dedent(
            """\
            <inputs>
                <tension_curve>
                    {tension_curve}
                </tension_curve>
                <pacing_curve>
                    {pacing_curve}
                </pacing_curve>
                <scene_length_distribution> 
                    {scene_length_distribution}
                </scene_length_distribution>
                <recent_chapter_rythm>
                    {recent_chapter_rythm}
                </recent_chapter_rythm>
            </inputs>
            """
        ),
        "world": textwrap.dedent(
            """\
            <inputs>
                <entity_ledger>
                    {entity_ledger}
                </entity_ledger>
                <contradictions>
                    {contradictions}
                </contradictions>
            </inputs>
            """
        )
    }

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        story_repo: StoryRepository,
        chapter_repo: ChapterRepository,
        scene_repo: SceneRepository,
        provider: AIProvider,
        redis: aioredis.Redis
    ):
        self._analytics_repo = analytics_repo
        self._story_repo = story_repo
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo
        self._provider = provider 
        self._cache = redis


    def _get_cache_key(
        self,
        story_id: str,
        user_id: str,
        extraction: Literal["plot_threads", "act_segmentation", "contradictions", "entities"]
    ) -> str:
        return f"{extraction}:{story_id}:{user_id}"
    
    
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

    
    async def get_prompt_inputs(
        self,
        story_id: str,
        user_id: str,
        lense: Literal["character", "plot", "structure", "world"]
    ) -> dict:
        
        match lense:

            case "character":
                cast_statistics, co_occurence_statistics, character_statistics = \
                    await asyncio.gather(
                        self._analytics_repo.get_cast_statistics(story_id, user_id),
                        self._analytics_repo.get_character_co_occurence_statistics(story_id, user_id),
                        self._analytics_repo.get_character_statistics(story_id, user_id)
                    )                    
                
                cast_statistics_table = PrettyTable(["pov", "scene_count", "word_count"])
                for cast_row in cast_statistics:
                    cast_statistics_table.add_row([*cast_row])
                
                co_occurence_statistics_table = PrettyTable(["character_a", "character_b", "scene_count", "word_count"])
                for co_occur_row in co_occurence_statistics:
                    co_occurence_statistics_table.add_row([*co_occur_row])

                character_statistics_table = PrettyTable(["chapter_id", "chapter_number", "pov", "scene_count", "word_count"])
                for character_row in character_statistics:
                    character_statistics_table.add_row([*character_row])

                return {
                    "cast_statistics": cast_statistics_table.get_string(),
                    "co_occurence_statistics": co_occurence_statistics_table.get_string(),
                    "character_statistics": character_statistics_table.get_string()
                }

            case "plot":
                plot_threads, act_segmentation = \
                    await asyncio.gather(
                        self.extract_plot_threads(story_id, user_id),
                        self.extract_acts(story_id, user_id)
                    )
                
                if (
                    plot_threads.extraction.threads is None 
                    or act_segmentation.extraction.acts is None
                ):
                    raise ServiceError("scv.analytics.get_prompt_inputs.failed")

                plot_threads_table = PrettyTable(["name", "chapter_started", "chapter_ended", "chapter_last_touched", "status"])
                for thread in plot_threads.extraction.threads:
                    plot_threads_table.add_row([
                        thread.name, 
                        thread.chapter_started, 
                        thread.chapter_ended, 
                        thread.chapter_last_touched, 
                        thread.status
                    ])
                
                acts_table = PrettyTable(["number", "chapter_started", "chapter_ended", "current_chapter"])
                for act in act_segmentation.extraction.acts: 
                    acts_table.add_row([
                        act.number,
                        act.chapter_started,
                        act.chapter_ended,
                        act.current_chapter
                    ])

                return {
                    "plot_threads": plot_threads_table.get_string(),
                    "act_segmentation": acts_table.get_string()
                }


            case "structure":
                tension_and_pacing_curves, scene_length_distribution, recent_chapter_rythm = \
                    await asyncio.gather(
                        self.get_tension_and_pacing_curves(story_id, user_id),
                        self.get_scene_length_distribution(story_id, user_id),
                        self.get_recent_chapters_rythm(story_id, user_id)
                    )
                
                tension_curve_table = PrettyTable(["chapter_id", "chapter_number", "avg_tension"])
                for tension_row in tension_and_pacing_curves.tension_curve:
                    tension_curve_table.add_row([tension_row.chapter_id, tension_row.chapter_number, tension_row.avg_tension])

                pacing_curve_table = PrettyTable(["chapter_id", "chapter_number", "avg_tension"])
                for pacing_row in tension_and_pacing_curves.pacing_curve:
                    pacing_curve_table.add_row([pacing_row.chapter_id, pacing_row.chapter_number, pacing_row.avg_pacing])

                scene_length_distribution_table = PrettyTable(["bin", "count"])
                for length_row in scene_length_distribution.distribution:
                    scene_length_distribution_table.add_row([length_row.bin, length_row.count])
                
                recent_rythm_table = PrettyTable(["chapter_id", "chapter_number", "avg_tension", "avg_pacing"])
                for tension_row, pacing_row in zip(recent_chapter_rythm.tension_curve, recent_chapter_rythm.pacing_curve):
                    recent_rythm_table.add_row([tension_row.chapter_id, tension_row.chapter_number, tension_row.avg_tension, pacing_row.avg_pacing])

                return {
                    "tension_curve": tension_curve_table.get_string(),
                    "pacing_curve": pacing_curve_table.get_string(),
                    "scene_length_distribution": scene_length_distribution_table.get_string(),
                    "recent_chapter_rythm": recent_rythm_table.get_string()
                }

            case "world":
                
                entity_ledger, contradictions = \
                    await asyncio.gather(
                        self.extract_entities(story_id, user_id),
                        self.extract_contradictions(story_id, user_id)
                    )
                
                if (
                    entity_ledger.extraction.entities is None 
                    or contradictions.extraction.contradictions is None
                ):
                    raise ServiceError("scv.analytics.get_prompt_inputs.failed")

                entity_ledger_table = PrettyTable(["type", "name", "chapter_first_appeared", "chapter_last_touched"])
                for entity in entity_ledger.extraction.entities:
                    entity_ledger_table.add_row([entity.type, entity.name, entity.chapter_first_appeared, entity.chapter_last_touched])

                contradictions_table = PrettyTable(["headline", "report", "relevant_chapters"])
                for contradiction in contradictions.extraction.contradictions:
                    chapters = ", ".join([str(chapter) for chapter in contradiction.relevant_chapters])
                    contradictions_table.add_row([
                        contradiction.headline,
                        contradiction.report,
                        chapters
                    ])

                return {
                    "entity_ledger": entity_ledger_table.get_string(),
                    "contradictions": contradictions_table.get_string()
                }

    async def get_analytics_suggestion(
        self,
        story_id: str,
        user_id: str,
        lense: Literal["character", "plot", "structure", "world"],
        ignore_cache: bool = False
    ) -> AnalyticsSuggestionResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        cache_key = f"suggestion:{lense}:{story_id}:{user_id}"
        
        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return AnalyticsSuggestionResponse.model_validate_json(raw_data)
        
        inputs = await self.get_prompt_inputs(story_id, user_id, lense)

        prompt_template = self.prompt_template_map.get(lense)
        system_prompt = self.prompt_map.get(lense)

        if prompt_template is None:
            raise ServiceError("Invalid lense! Must be 'character', 'plot', 'structure', or 'world'.")
        
        if system_prompt is None:
            raise ServiceError("Invalid lense! Must be 'character', 'plot', 'structure', or 'world'.")

        prompt = prompt_template.format(**inputs)

        suggestion = await self._provider.extract(
            system_prompt=system_prompt,
            text=prompt,
            max_tokens=config.ai.suggestion_max_tokens,
            schema=AnalyticsSuggestionExtraction
        )

        response = AnalyticsSuggestionResponse(
            story_id=story.id,
            story_title=story.title,
            generated_at=datetime.now(tz=tz.utc),
            suggestion=suggestion
        )

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(hours=1))

        return response


    async def get_cast_statistics(
        self,
        story_id: str,
        user_id: str
    ) -> CastStatisticsResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        rows = await self._analytics_repo.get_cast_statistics(story_id, user_id)

        return CastStatisticsResponse(
            story_id=story.id,
            story_title=story.title,
            statistics=[
                CastStatisticsRow(
                    character=row[0],
                    scene_count=row[1],
                    word_count=row[2]
                )
                for row in rows
            ]
        )
    
    async def get_co_occurence_statistics(
        self,
        story_id: str,
        user_id: str
    ) -> CoOccurenceStatisticsResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        rows = await self._analytics_repo.get_character_co_occurence_statistics(story_id, user_id)

        return CoOccurenceStatisticsResponse(
            story_id=story.id,
            story_title=story.title,
            statistics=[
                CoOccurenceStatisticsRow(
                    character_a=row[0],
                    character_b=row[1],
                    scene_count=row[2],
                    word_count=row[3]
                )
                for row in rows
            ]
        )
    
    async def get_character_statistics(
        self,
        story_id: str,
        user_id: str
    ) -> CharacterStatisticsResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        rows = await self._analytics_repo.get_character_statistics(story_id, user_id)

        return CharacterStatisticsResponse(
            story_id=story.id,
            story_title=story.title,
            statistics=[
                CharacterStatisticsRow(
                    chapter_id=row[0],
                    chapter_number=row[1],
                    pov=row[2],
                    scene_count=row[3],
                    word_count=row[4]
                )
                for row in rows
            ]
        )
    

    async def get_scene_length_distribution(
        self,
        story_id: str,
        user_id: str
    ) -> SceneLengthDistributionResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        rows = await self._analytics_repo.get_scene_length_distribution(story_id, user_id)
        
        return SceneLengthDistributionResponse(
            story_id=story.id,
            story_title=story.title,
            distribution=[
                SceneLengthDistributionRow(
                    bin=row[0],
                    count=row[1]
                )
                for row in rows
            ]
        )
    
    async def get_tension_and_pacing_curves(
        self,
        story_id: str,
        user_id: str
    ) -> TensionAndPacingCurveResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")

        rows = await self._analytics_repo.get_tension_and_pacing_curves(story_id, user_id)

        return TensionAndPacingCurveResponse(
            story_id=story.id,
            story_title=story.title,
            tension_curve=[
                TensionCurveRow(
                    chapter_id=row[0],
                    chapter_number=row[1],
                    avg_tension=row[2]
                )
                for row in rows
            ],
            pacing_curve=[
                PacingCurveRow(
                    chapter_id=row[0],
                    chapter_number=row[1],
                    avg_pacing=row[3]
                )
                for row in rows
            ]
        )
    
    async def get_recent_chapters_rythm(
        self,
        story_id: str,
        user_id: str
    ) -> TensionAndPacingCurveResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")

        rows = await self._analytics_repo.get_recent_chapters_rythm(story_id, user_id)

        return TensionAndPacingCurveResponse(
            story_id=story.id,
            story_title=story.title,
            tension_curve=[
                TensionCurveRow(
                    chapter_id=row[0],
                    chapter_number=row[1],
                    avg_tension=row[2]
                )
                for row in rows
            ],
            pacing_curve=[
                PacingCurveRow(
                    chapter_id=row[0],
                    chapter_number=row[1],
                    avg_pacing=row[3]
                )
                for row in rows
            ]
        )
    
    async def extract_plot_threads(
        self,
        story_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> PlotThreadsResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        cache_key = self._get_cache_key(story_id, user_id, "plot_threads")
        
        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return PlotThreadsResponse.model_validate_json(raw_data)
        
        story_context = await self.story_service.get_story_context(user_id, story_id)
        
        extraction = await self._provider.extract(
            system_prompt=PLOT_THREADS_EXTRACTION_PROMPT,
            text=f"""\
            <story_context>
                {story_context}
            </story_context>
            """,
            max_tokens=config.ai.plot_threads_max_tokens,
            schema=PlotThreadsExtraction
        )

        response = PlotThreadsResponse(
            story_id=story.id,
            story_title=story.title,
            path_array=story.path_array if story.path_array else [],
            generated_at=datetime.now(tz=tz.utc),
            extraction=extraction
        )

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(hours=1))

        return response
            
    async def extract_acts(
        self,
        story_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> ActSegmentationResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        cache_key = self._get_cache_key(story_id, user_id, "act_segmentation")
        
        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return ActSegmentationResponse.model_validate_json(raw_data)
        
        story_context = await self.story_service.get_story_context(user_id, story_id)
        
        extraction = await self._provider.extract(
            system_prompt=ACT_SEGMENTATION_EXTRACTION_PROMPT,
            text=f"""\
            <story_context>
                {story_context}
            </story_context>
            """,
            max_tokens=config.ai.act_segmentation_max_tokens,
            schema=ActSegmentationExtraction
        )

        response = ActSegmentationResponse(
            story_id=story.id,
            story_title=story.title,
            path_array=story.path_array if story.path_array else [],
            generated_at=datetime.now(tz=tz.utc),
            extraction=extraction
        )

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(hours=1))

        return response  

    async def extract_contradictions(
        self,
        story_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> ContradictionResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        cache_key = self._get_cache_key(story_id, user_id, "contradictions")
        
        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return ContradictionResponse.model_validate_json(raw_data)
        
        story_context = await self.story_service.get_story_context(user_id, story_id)
        
        extraction = await self._provider.extract(
            system_prompt=CONTRADICTION_EXTRACTION_PROMPT,
            text=f"""\
            <story_context>
                {story_context}
            </story_context>
            """,
            max_tokens=config.ai.contradictions_max_tokens,
            schema=ContradictionExtraction
        )

        response = ContradictionResponse(
            story_id=story.id,
            story_title=story.title,
            path_array=story.path_array if story.path_array else [],
            generated_at=datetime.now(tz=tz.utc),
            extraction=extraction
        )

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(hours=1))

        return response  
    
    async def extract_entities(
        self,
        story_id: str,
        user_id: str,
        ignore_cache: bool = False
    ) -> EntityLedgerResponse:
        
        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        cache_key = self._get_cache_key(story_id, user_id, "entities")
        
        if not ignore_cache:
            if raw_data := (await self._cache.get(cache_key)):
                return EntityLedgerResponse.model_validate_json(raw_data)
        
        story_context = await self.story_service.get_story_context(user_id, story_id)
        
        extraction = await self._provider.extract(
            system_prompt=ENTITY_LEDGER_EXTRACTION_PROMPT,
            text=f"""\
            <story_context>
                {story_context}
            </story_context>
            """,
            max_tokens=config.ai.entities_max_tokens,
            schema=EntityLedgerExtraction
        )

        response = EntityLedgerResponse(
            story_id=story.id,
            story_title=story.title,
            path_array=story.path_array if story.path_array else [],
            generated_at=datetime.now(tz=tz.utc),
            extraction=extraction
        )

        await self._cache.set(cache_key, response.model_dump_json(), ex=timedelta(hours=1))

        return response  