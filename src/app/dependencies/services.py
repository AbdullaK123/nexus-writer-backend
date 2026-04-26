from functools import lru_cache

from fastapi import Request
from tortoise import Tortoise
from loguru import logger

from src.infrastructure.ai import OpenAIProvider, AIProvider
from src.infrastructure.db.postgres import TORTOISE_ORM


async def init_infrastructure() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("infra.db.connected")


async def shutdown_infrastructure() -> None:
    await Tortoise.close_connections()
    logger.info("infra.db.disconnected")


@lru_cache
def build_ai_provider() -> AIProvider:
    """Construct the singleton AI provider. Cached so repeated calls (lifespan,
    tests, scripts) share one client + concurrency semaphore."""
    return OpenAIProvider()


def get_ai_provider(request: Request) -> AIProvider:
    """FastAPI dependency. Reads the provider from app.state, where lifespan
    stashed it at startup. Override in tests via app.dependency_overrides."""
    return request.app.state.ai_provider