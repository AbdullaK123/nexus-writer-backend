import redis.asyncio as aioredis
from typing import AsyncGenerator
from fastapi import Depends

from src.infrastructure.redis.pool import get_pool
from src.infrastructure.redis.pubsub import RedisPubSub


async def get_redis(
    pool: aioredis.ConnectionPool = Depends(get_pool),
) -> AsyncGenerator[aioredis.Redis, None]:
    async with aioredis.Redis(connection_pool=pool) as client:
        yield client


async def get_pubsub(
    redis: aioredis.Redis = Depends(get_redis),
) -> RedisPubSub:
    return RedisPubSub(redis)
