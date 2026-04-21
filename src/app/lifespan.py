from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()

    yield

    logger.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()
    await logger.complete()
