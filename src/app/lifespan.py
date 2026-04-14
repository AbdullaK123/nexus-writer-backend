from src.service.workers import AsyncBackgroundWorker
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config.logging import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
from src.app.di import container


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    logger.info("Initializing DI container resources...")
    await container.init_resources()  # type: ignore[misc]

    session_cleaner = AsyncBackgroundWorker()

    session_cleaner.schedule_cron_job(
        cleanup_expired_sessions_batched,
        cron_expr="0 * * * *"
    )

    logger.info("Starting session cleanup background worker...")
    await session_cleaner.start()

    yield

    logger.info("Removing all jobs...")
    session_cleaner.remove_all_jobs()

    logger.info("Shutting down session cleanup background worker")
    await session_cleaner.stop()

    logger.info("Shutting down DI container resources...")
    await container.shutdown_resources()  # type: ignore[misc]