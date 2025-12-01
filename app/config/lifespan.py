from app.workers import AsyncBackgroundWorker
from app.jobs.session import cleanup_expired_sessions_batched
from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
from langchain_community.graphs import Neo4jGraph
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

    yield

    logger.info("Removing all jobs...")
    session_cleaner.remove_all_jobs()

    logger.info("Shutting down session cleanup background worker")
    await session_cleaner.stop()