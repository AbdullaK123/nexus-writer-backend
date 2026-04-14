from src.infrastructure.config import settings
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from typing import Dict, List, Any, Optional
from src.service.target.service import TargetService
from src.data.schemas import TargetResponse
from src.shared.utils.decorators import log_errors
from src.data.schemas.analytics import WritingSession, StoryAnalyticsResponse
from src.data.models import FrequencyType
from datetime import datetime, timezone
from datetime import timedelta
from src.service.exceptions import NotFoundError, ValidationError
from src.service.story.service import StoryService
from src.data.repositories.analytics.analytics import AnalyticsRepo
from pymongo.asynchronous.database import AsyncDatabase


class AnalyticsService:

    def __init__(self, repo: AnalyticsRepo, story_service: StoryService, target_service: TargetService):
        self.repo = repo
        self.story_service = story_service
        self.target_service = target_service

    async def get_writing_kpis(
            self,
            story_id: str,
            user_id: str,
            frequency: FrequencyType,
    ) -> Dict[str, Any]:

        if frequency == "Daily":
            time_filter = "started::date = CURRENT_DATE"
        elif frequency == "Weekly":
            time_filter = "started::date >= CURRENT_DATE - INTERVAL '7 days'"
        else:  # Monthly
            time_filter = "started::date >= CURRENT_DATE - INTERVAL '30 days'"

        return await self.repo.get_kpis(story_id, user_id, time_filter)

    async def get_writing_output_over_time(
            self,
            story_id: str,
            user_id: str,
            frequency: FrequencyType,
            from_date: datetime,
            to_date: datetime
    ) -> List[Dict[str, Any]]:

        if to_date < from_date:
            raise ValidationError(
                message="The end date must be after the start date."
            )

        from_date_str = from_date.date().isoformat()
        to_date_str = to_date.date().isoformat()

        if frequency == "Daily":
            query = """
                    SELECT 
                        started::date as date,
                        SUM(words_written) as total_words
                    FROM writing_sessions
                    WHERE story_id = ?
                      AND user_id = ?
                      AND started:: date BETWEEN ? AND ?
                    GROUP BY started:: date
                    ORDER BY date 
                    """
        elif frequency == "Weekly":
            query = """
                    SELECT 
                        DATE_TRUNC('week', started)::date as week_start,
                        EXTRACT(week FROM started)  as week_num, 
                        SUM(words_written)          as total_words
                    FROM writing_sessions
                    WHERE story_id = ?
                      AND user_id = ?
                      AND started::date BETWEEN ? AND ?
                    GROUP BY DATE_TRUNC('week', started)::date, EXTRACT (week FROM started)
                    ORDER BY week_start 
                    """
        else:  # Monthly
            query = """
                    SELECT 
                        DATE_TRUNC('month', started)::date as month_start, 
                        MONTHNAME(started)           as month_name, 
                        SUM(words_written)           as total_words
                    FROM writing_sessions
                    WHERE story_id = ?
                      AND user_id = ?
                      AND started::date BETWEEN ? AND ?
                    GROUP BY DATE_TRUNC('month', started)::date, MONTHNAME(started)
                    ORDER BY month_start 
                    """

        return await self.repo.get_words_over_time(
            story_id, user_id, query, from_date_str, to_date_str
        )

    @log_errors
    async def get_story_analytics(
            self,
            story_id: str,
            user_id: str,
            frequency: FrequencyType,
            from_date: datetime = datetime.now(timezone.utc) - timedelta(days=30),
            to_date: datetime = datetime.now(timezone.utc)
    ) -> StoryAnalyticsResponse:

        story = await self.story_service.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        kpis = await self.get_writing_kpis(
            story_id=story_id,
            user_id=user_id,
            frequency=frequency
        )

        words_over_time = await self.get_writing_output_over_time(
            story_id=story_id,
            user_id=user_id,
            frequency=frequency,
            from_date=from_date,
            to_date=to_date
        )

        target = await self.target_service.get_target_by_story_id_and_frequency(
            story_id,
            user_id,
            frequency
        )

        return StoryAnalyticsResponse(
            kpis=kpis,
            words_over_time=words_over_time,
            target=target if target else TargetResponse(frequency=frequency, story_id=story_id)
        )

    @log_errors
    async def write_session(self, session_data: WritingSession) -> WritingSession:
        session_dict = session_data.model_dump()
        result = await self.repo.insert_session(session_dict)

        return WritingSession(
            id=result['id'],
            started=session_data.started,
            ended=session_data.ended,
            user_id=result['user_id'],
            story_id=result['story_id'],
            chapter_id=result['chapter_id'],
            words_written=result['words_written']
        )


