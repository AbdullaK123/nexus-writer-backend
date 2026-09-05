import redis.asyncio as aioredis


_FIXED_WINDOW_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


async def consume_fixed_window(
    redis: aioredis.Redis,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """Atomically consume one request from a fixed-window Redis counter."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")

    count = await redis.eval(
        _FIXED_WINDOW_SCRIPT,
        1,
        key,
        window_seconds,
    )
    return int(count) <= limit
