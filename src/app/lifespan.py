from src.service.workers import AsyncBackgroundWorker
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config.logging import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from src.infrastructure.config import config as app_config
from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure

log = get_layer_logger(LAYER_APP)


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    log.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()

    session_cleaner = AsyncBackgroundWorker()

   
    session_cleaner.schedule_cron_job(
        cleanup_expired_sessions_batched,
        cron_expr=app_config.jobs.session_cleanup_cron
    )

    log.info("Lifecycle starting: session cleanup worker scheduled", cron=app_config.jobs.session_cleanup_cron)
    await session_cleaner.start()

    yield

    log.info("Lifecycle shutdown: removing scheduled jobs")
    session_cleaner.remove_all_jobs()

    log.info("Lifecycle shutdown: stopping session cleanup worker")
    await session_cleaner.stop()

    log.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()