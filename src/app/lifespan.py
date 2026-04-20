from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from src.app.jobs import (
    run_all_jobs,
    stop_all_jobs,
    start_all_jobs,
)

log = get_layer_logger(LAYER_APP)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()

    # to catch stale summaries during downtime
    asyncio.create_task(run_all_jobs())

    start_all_jobs()

    yield

    stop_all_jobs()

    log.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()
