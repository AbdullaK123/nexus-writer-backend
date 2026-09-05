import time

import redis.asyncio as aioredis
from typing import AsyncGenerator
from fastapi import Depends, Request
from src.infrastructure.redis.pool import get_pool
from src.infrastructure.redis.pubsub import RedisPubSub
from src.infrastructure.redis.rate_limiting import check_rate_limit


async def get_redis(
    pool: aioredis.ConnectionPool = Depends(get_pool),
) -> AsyncGenerator[aioredis.Redis, None]:
    async with aioredis.Redis(connection_pool=pool) as client:
        yield client

async def get_pubsub(
    redis: aioredis.Redis = Depends(get_redis)
) -> RedisPubSub:
    return RedisPubSub(redis)

def rate_limit(
    *,
    prefix: str,
    limit: int,
    window: int,
):
    async def dependency(request: Request):
        redis = request.app.state.redis
        ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")
        key = f"rl:{prefix}:{ip}:{int(time.time()) // window}"
        await check_rate_limit(redis, key=key, limit=limit, window_seconds=window)
    return Depends(dependency)

# Reusable rate limit tiers
auth_rate_limit = rate_limit(prefix="auth", limit=10, window=60)
write_rate_limit = rate_limit(prefix="write", limit=30, window=60)
ai_rate_limit = rate_limit(prefix="ai", limit=15, window=60)
read_rate_limit = rate_limit(prefix="read", limit=200, window=60)