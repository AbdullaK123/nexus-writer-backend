from tortoise import Tortoise
from loguru import logger

from src.infrastructure.db.postgres import TORTOISE_ORM


async def init_infrastructure() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("infra.db.connected")


async def shutdown_infrastructure() -> None:
    await Tortoise.close_connections()
    logger.info("infra.db.disconnected")
