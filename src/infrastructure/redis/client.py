"""Redis client access — use the dependency functions instead of calling these directly."""
from redis.asyncio import Redis


def get_redis() -> Redis:
    """Return a Redis client from the managed pool."""
    from src.app.dependencies.services import get_redis_client
    return get_redis_client()
