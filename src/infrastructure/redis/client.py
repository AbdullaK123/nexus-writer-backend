"""Redis client access — use the DI container instead of calling these directly."""
from redis import Redis


def get_redis() -> Redis:
    """Return a Redis client from the DI container's managed pool."""
    from src.infrastructure.di import container
    return container.redis_client()
