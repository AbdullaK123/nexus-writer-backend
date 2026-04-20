from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP

log = get_layer_logger(LAYER_APP)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()

    yield

    log.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()
