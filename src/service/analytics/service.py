from typing import Literal

from src.service.exceptions import NotFoundError
from src.data.repositories.analytics import AnalyticsRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.analytics import AnalyticsSuggestionResponse, CastStatisticsResponse, CastStatisticsRow, CharacterStatisticsResponse, CharacterStatisticsRow, CoOccurenceStatisticsResponse, CoOccurenceStatisticsRow, PacingCurveRow, SceneLengthDistributionResponse, SceneLengthDistributionRow, TensionAndPacingCurveResponse, TensionCurveRow
from src.infrastructure.ai.providers.protocol import AIProvider


class AnalyticsService:

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        story_repo: StoryRepository,
        provider: AIProvider
    ):
        self._analytics_repo = analytics_repo
        self._story_repo = story_repo
        self._provider = provider 


    async def get_analytics_suggestion(
        self,
        story_id: str,
        user_id: str,
        lense: Literal["character", "plot", "structure", "world"]
    ) -> AnalyticsSuggestionResponse:
        raise NotImplementedError()


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