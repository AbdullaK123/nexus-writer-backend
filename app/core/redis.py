from redis import Redis, ConnectionPool
from app.config.settings import app_config

pool = ConnectionPool.from_url(app_config.redis_url)

def get_redis() -> Redis:
    return Redis(connection_pool=pool)