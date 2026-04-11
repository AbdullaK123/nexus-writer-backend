from src.service.workers import AsyncBackgroundWorker
from src.service.jobs.session import cleanup_expired_sessions_batched
from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
from src.infrastructure.di import container
from tortoise import Tortoise
from src.infrastructure.db.postgres import TORTOISE_ORM


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Initializing Tortoise ORM...")
    await Tortoise.init(config=TORTOISE_ORM)

    logger.info("Initializing DI container resources...")
    await container.init_resources()

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
    await container.shutdown_resources()

    logger.info("Closing Tortoise ORM connections...")
    await Tortoise.close_connections()