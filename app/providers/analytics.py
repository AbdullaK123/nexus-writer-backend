import duckdb
from app.config.settings import app_config
from loguru import logger
from typing import Dict, List, Any, Tuple, Optional
from app.utils.decorators import log_errors
from app.schemas.analytics import WritingSession
import asyncio
import time


class AnalyticsProvider:

    def __init__(self):
        self.motherduck_url = app_config.motherduck_url
        logger.info("🦆 AnalyticsProvider initialized", motherduck_url=self.motherduck_url[:50] + "..." if len(self.motherduck_url) > 50 else self.motherduck_url)

    @log_errors
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        logger.debug("🔌 Establishing DuckDB connection", extra={"db_operation": True})
        start_time = time.time()
        
        conn = duckdb.connect(self.motherduck_url)
        connection_time = round((time.time() - start_time) * 1000, 2)
        
        logger.success(
            "✅ DuckDB connection established",
            connection_time_ms=connection_time,
            extra={"db_operation": True, "performance_tracking": True}
        )
        return conn
    
    @log_errors
    def sql(
        self,
        query: str, 
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        logger.debug(
            "📊 Executing SQL query",
            query_preview=query[:100] + "..." if len(query) > 100 else query,
            params_count=len(params) if params else 0,
            extra={"db_operation": True}
        )
        
        start_time = time.time()
        
        with self._get_connection() as conn:
            result_df = conn.execute(query, params).fetch_df()
            records = result_df.to_dict('records')
            
        execution_time = round((time.time() - start_time) * 1000, 2)
        
        logger.success(
            "🎯 SQL query executed successfully",
            records_returned=len(records),
            execution_time_ms=execution_time,
            query_type="SELECT" if query.strip().upper().startswith("SELECT") else "INSERT/UPDATE/DELETE",
            extra={"db_operation": True, "performance_tracking": True}
        )
        
        return records
        
    @log_errors
    def _write_session_sync(self, session_data: WritingSession) -> WritingSession:
        logger.info(
            "💾 Writing session to DuckDB",
            session_id=session_data.id,
            user_id=session_data.user_id,
            story_id=session_data.story_id,
            chapter_id=session_data.chapter_id,
            words_written=session_data.words_written,
            duration_seconds=round((session_data.ended - session_data.started).total_seconds(), 2),
            extra={"db_operation": True}
        )
        
        start_time = time.time()
        
        # ✅ UPSERT QUERY - HANDLES DUPLICATES GRACEFULLY
        result = self.sql(
            """
            INSERT INTO writing_sessions (id, started, ended, user_id, story_id, chapter_id, words_written)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                ended = EXCLUDED.ended,
                words_written = EXCLUDED.words_written
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
        
        if not result:
            raise ValueError("UPSERT query returned no results")
        
        saved_session = WritingSession(**result[0])
        write_time = round((time.time() - start_time) * 1000, 2)
        
        logger.success(
            "🚀 Writing session saved successfully",
            session_id=saved_session.id,
            user_id=saved_session.user_id,
            words_written=saved_session.words_written,
            write_time_ms=write_time,
            extra={"db_operation": True, "performance_tracking": True, "analytics_success": True}
        )
        
        return saved_session
    
    @log_errors
    async def write_session(self, session_data: WritingSession) -> WritingSession:
        logger.debug(
            "🔄 Converting sync write_session to async",
            session_id=session_data.id,
            extra={"job_type": "background_task"}
        )
        
        start_time = time.time()
        
        result = await asyncio.to_thread(self._write_session_sync, session_data)
        async_time = round((time.time() - start_time) * 1000, 2)
        
        logger.success(
            "⚡ Async session write completed",
            session_id=result.id,
            total_async_time_ms=async_time,
            extra={"job_type": "background_task", "performance_tracking": True}
        )
        
        return result