"""DI container for Prefect flow infrastructure.

Initialised once in the worker process before any flows run.
Flows and tasks use Tortoise / MongoDB globals after init — no per-flow setup.
"""
from dependency_injector import containers, providers
from tortoise import Tortoise

from src.infrastructure.config import settings
from src.infrastructure.db.mongodb import MongoDB
from src.infrastructure.db.postgres import TORTOISE_ORM


async def _init_tortoise():
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await Tortoise.close_connections()


async def _init_mongodb():
    await MongoDB.connect(settings.mongodb_url)
    yield MongoDB.db
    await MongoDB.close()


class FlowContainer(containers.DeclarativeContainer):
    """Slim container for the worker process — just databases + redis url."""

    tortoise = providers.Resource(_init_tortoise)
    mongodb = providers.Resource(_init_mongodb)
    redis_url = providers.Object(settings.redis_url)
