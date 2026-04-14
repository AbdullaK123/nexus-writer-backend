from src.service.workers import AsyncBackgroundWorker
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config.logging import setup_logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from src.app.di import container

log = get_layer_logger(LAYER_APP)


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    log.info("Lifecycle starting: initialising DI container resources")
    await container.init_resources()  # type: ignore[misc]

    session_cleaner = AsyncBackgroundWorker()

    session_cleaner.schedule_cron_job(
        cleanup_expired_sessions_batched,
        cron_expr="0 * * * *"
    )

    log.info("Lifecycle starting: session cleanup worker scheduled (cron='0 * * * *')")
    await session_cleaner.start()

    yield

    log.info("Lifecycle shutdown: removing scheduled jobs")
    session_cleaner.remove_all_jobs()

    log.info("Lifecycle shutdown: stopping session cleanup worker")
    await session_cleaner.stop()

    log.info("Lifecycle shutdown: releasing DI container resources")
    await container.shutdown_resources()  # type: ignore[misc]