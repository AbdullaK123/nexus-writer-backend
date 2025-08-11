import duckdb
from app.config.settings import app_config
from loguru import logger
from typing import Dict, List, Any, Tuple, Optional
from app.utils.decorators import log_errors
from app.schemas.analytics import WritingSession
import asyncio


class AnalyticsProvider:

    def __init__(self):
        self.motherduck_url = app_config.motherduck_url

    @log_errors
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.motherduck_url)
    
    @log_errors
    def sql(
        self,
        query: str, 
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            return (
                conn.execute(query, params)
                    .fetch_df()
                    .to_dict('records')
            )
        
    def _write_session_sync(self, session_data: WritingSession) -> WritingSession:
        result = self.sql(
            """
            INSERT INTO writing_sessions (id, started, ended, user_id, story_id, chapter_id, words_written)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (
                session_data.id,
                session_data.started,
                session_data.ended,
                session_data.user_id,
                session_data.story_id,
                session_data.chapter_id,
                session_data.words_written
            )
        )
        return WritingSession(**result[0])
    
    async def write_session(self, session_data: WritingSession) -> WritingSession:
        return await asyncio.to_thread(self._write_session_sync, session_data)
