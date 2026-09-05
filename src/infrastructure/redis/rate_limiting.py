import time

from src.service.exceptions import RateLimitError

async def check_rate_limit(
    redis,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = time.time()
    window_start = now - window_seconds

    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(key, 0, window_start)  # drop expired entries
        pipe.zadd(key, {f"{now}": now})               # add this request
        pipe.zcard(key)                                # count requests in window
        pipe.expire(key, window_seconds + 1)           # auto-cleanup
        results = await pipe.execute()

    count = results[2]
    if count > limit:
        raise RateLimitError("Too many requests. Please try again later.")