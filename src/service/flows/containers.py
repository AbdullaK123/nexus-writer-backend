"""Async context manager for worker infrastructure.

Initialised once in the worker process before any jobs run.
Jobs use Tortoise / MongoDB globals after init — no per-job setup.
"""
from contextlib import asynccontextmanager
from tortoise import Tortoise

from src.infrastructure.config import settings, config
from src.infrastructure.db.mongodb import MongoDB
from src.infrastructure.db.postgres import TORTOISE_ORM


@asynccontextmanager
async def flow_lifespan():
    """Bring up and tear down Tortoise + MongoDB for the worker process."""
    await Tortoise.init(config=TORTOISE_ORM)
    await MongoDB.connect(settings.mongodb_url, config.mongo.database_name)
    try:
        yield
    finally:
        await MongoDB.close()
        await Tortoise.close_connections()
