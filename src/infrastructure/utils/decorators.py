import functools

from src.infrastructure.exceptions import DatabaseError, RedisError
from src.shared.utils.logging_context import get_layer_logger, LAYER_INFRA

log = get_layer_logger(LAYER_INFRA)


def handle_db_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError:
            raise
        except Exception as e:
            log.error(f"DB error in {func.__qualname__}: {e}")
            raise DatabaseError(str(e), original=e)

    return wrapper


def handle_redis_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RedisError:
            raise
        except Exception as e:
            log.error(f"Redis error in {func.__qualname__}: {e}")
            raise RedisError(str(e), original=e)

    return wrapper
