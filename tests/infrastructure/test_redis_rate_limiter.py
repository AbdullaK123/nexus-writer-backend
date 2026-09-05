import asyncio

from redis.asyncio import Redis

from src.infrastructure.redis.rate_limiting import consume_fixed_window


async def test_fixed_window_allows_exactly_limit(redis_client: Redis) -> None:
    key = "test:rate-limit:boundary"

    results = [
        await consume_fixed_window(
            redis_client,
            key=key,
            limit=3,
            window_seconds=60,
        )
        for _ in range(4)
    ]

    assert results == [True, True, True, False]
    ttl = await redis_client.ttl(key)
    assert 0 < ttl <= 60


async def test_fixed_window_is_atomic_under_concurrency(redis_client: Redis) -> None:
    key = "test:rate-limit:race"

    results = await asyncio.gather(*(
        consume_fixed_window(
            redis_client,
            key=key,
            limit=10,
            window_seconds=60,
        )
        for _ in range(100)
    ))

    assert sum(results) == 10


async def test_fixed_window_keys_are_independent(redis_client: Redis) -> None:
    first = await consume_fixed_window(
        redis_client,
        key="test:rate-limit:user-a",
        limit=1,
        window_seconds=60,
    )
    first_over = await consume_fixed_window(
        redis_client,
        key="test:rate-limit:user-a",
        limit=1,
        window_seconds=60,
    )
    second = await consume_fixed_window(
        redis_client,
        key="test:rate-limit:user-b",
        limit=1,
        window_seconds=60,
    )

    assert first is True
    assert first_over is False
    assert second is True
