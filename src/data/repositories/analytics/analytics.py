import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import duckdb
from src.shared.utils.logging_context import get_layer_logger, LAYER_DATA

log = get_layer_logger(LAYER_DATA)

from src.infrastructure.utils.retry import retry_network


class AnalyticsRepo:

    def __init__(self, motherduck_url: str):
        self.motherduck_url = motherduck_url

    @retry_network
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.motherduck_url)

    @retry_network
    def _sql_sync(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            result_df = conn.execute(query, params).fetch_df()
            return result_df.to_dict("records")

    async def sql(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._sql_sync, query, params)

    async def get_kpis(
        self, story_id: str, user_id: str, time_filter: str
    ) -> Dict[str, Any]:
        result = (await self.sql(
            f"""
            SELECT
                COALESCE(SUM(words_written), 0) as total_words,
                COALESCE(SUM(duration), 0) as total_duration,
                COALESCE(AVG(words_per_minute), 0) as avg_words_per_minute
            FROM writing_sessions
            WHERE story_id = ?
            AND user_id = ?
            AND {time_filter}
            """,
            (story_id, user_id),
        ))[0]
        return result

    async def get_words_over_time(
        self,
        story_id: str,
        user_id: str,
        query: str,
        from_date_str: str,
        to_date_str: str,
    ) -> List[Dict[str, Any]]:
        return await self.sql(query, (story_id, user_id, from_date_str, to_date_str))

    @staticmethod
    def _convert_uuid_fields(record: dict) -> dict:
        converted = {}
        for key, value in record.items():
            if isinstance(value, UUID):
                converted[key] = str(value)
            else:
                converted[key] = value
        return converted

    def _insert_session_sync(self, session_dict: dict) -> dict:
        analytics_session_id = str(uuid.uuid4())

        # Ensure string UUIDs
        for key in ["user_id", "story_id", "chapter_id"]:
            if isinstance(session_dict.get(key), UUID):
                session_dict[key] = str(session_dict[key])

        result = self._sql_sync(
            """
            INSERT INTO writing_sessions (id,
                                          started,
                                          ended,
                                          user_id,
                                          story_id,
                                          chapter_id,
                                          words_written)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *
            """,
            (
                analytics_session_id,
                session_dict["started"],
                session_dict["ended"],
                session_dict["user_id"],
                session_dict["story_id"],
                session_dict["chapter_id"],
                session_dict["words_written"],
            ),
        )

        if not result:
            raise ValueError("INSERT query returned no results")

        return self._convert_uuid_fields(result[0])

    async def insert_session(self, session_dict: dict) -> dict:
        return await asyncio.to_thread(self._insert_session_sync, session_dict)
