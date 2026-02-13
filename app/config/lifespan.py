from app.workers import AsyncBackgroundWorker
from app.jobs.session import cleanup_expired_sessions_batched
from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
from app.core.mongodb import MongoDB
from app.config.settings import app_config


@asynccontextmanager
async def lifespan(app: FastAPI):

    session_cleaner = AsyncBackgroundWorker()

    session_cleaner.schedule_cron_job(
        cleanup_expired_sessions_batched,
        cron_expr="0 * * * *"
    )

    logger.info("Starting session cleanup background worker...")
    await session_cleaner.start()

    logger.info("Connecting to mongo db database...")
    await MongoDB.connect(app_config.mongodb_url)

    yield

    logger.info("Removing all jobs...")
    session_cleaner.remove_all_jobs()

    logger.info("Shutting down session cleanup background worker")
    await session_cleaner.stop()

    logger.info("Closing connection to mongodb database...")
    await MongoDB.close()