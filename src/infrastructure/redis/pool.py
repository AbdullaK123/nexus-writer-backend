import redis.asyncio as aioredis
from src.infrastructure.config.settings import config, settings
from loguru import logger
import logfire

_pool: aioredis.ConnectionPool | None = None

def init_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is not None:
        return _pool
    _pool = aioredis.ConnectionPool.from_url(
        url=settings.redis_url,
        max_connections=config.redis.max_connections,
        decode_responses=config.redis.decode_responses
    )
    logger.info(
        "infra.redis_pool.connected",
        max_connections=config.redis.max_connections,
        decode_responses=config.redis.decode_responses
    )
    assert _pool is not None
    return _pool

async def close_pool() -> None:
    global _pool
    if _pool is None:
        return
    await _pool.disconnect()
    _pool = None
    logger.info("infra.redis_pool.disconnected")

def get_pool() -> aioredis.ConnectionPool:
    if _pool is None:
        raise RuntimeError("Redis pool not initialized - call init_pool() first")
    return _pool