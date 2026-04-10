from redis import Redis, ConnectionPool

from src.infrastructure.config.settings import settings

pool = ConnectionPool.from_url(settings.redis_url)


def get_redis() -> Redis:
    return Redis(connection_pool=pool)
