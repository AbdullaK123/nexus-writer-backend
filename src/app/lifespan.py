from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

from src.app.dependencies.services import (
    init_infrastructure,
    shutdown_infrastructure,
    build_ai_provider,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()
    app.state.ai_provider = build_ai_provider()

    yield

    logger.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()
    await logger.complete()
