from app.workers import AsyncBackgroundWorker
from app.jobs.session import cleanup_expired_sessions_with_analytics
from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):

    session_cleaner = AsyncBackgroundWorker()

    session_cleaner.start()

    await session_cleaner.schedule_cron_job(
        cleanup_expired_sessions_with_analytics,
        chron_expr="0 0 * * *"
    )

    yield

    session_cleaner.remove_all_jobs()

    session_cleaner.stop()