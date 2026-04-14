import functools
import logging
from uuid import UUID

from src.data.exceptions import NotFoundError as DataNotFound, DuplicateError
from src.infrastructure.exceptions import DatabaseError, RedisError
from src.service.exceptions import (
    ServiceError,
    NotFoundError,
    ConflictError,
    AuthError,
)

logger = logging.getLogger(__name__)


def handle_service_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServiceError:
            raise
        except DataNotFound as e:
            raise NotFoundError(f"{e.entity} not found")
        except DuplicateError as e:
            raise ConflictError(f"{e.entity} with this {e.field} already exists")
        except DatabaseError as e:
            logger.error(
                f"Infrastructure failure in {func.__qualname__}: {e.original}"
            )
            raise ServiceError("A database error occurred")
        except RedisError as e:
            logger.error(f"Cache failure in {func.__qualname__}: {e.original}")
            raise ServiceError("Cache unavailable")

    return wrapper


def validate(schema_class):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, data: dict, *args, **kwargs):
            from pydantic import ValidationError as PydanticError

            try:
                validated = schema_class(**data)
                return await func(self, validated, *args, **kwargs)
            except PydanticError as e:
                from src.service.exceptions import ValidationError

                fields: dict[str, list[str]] = {}
                for error in e.errors():
                    field = str(error["loc"][0])
                    fields.setdefault(field, []).append(error["msg"])
                raise ValidationError(fields)

        return wrapper

    return decorator


def require_auth(func):
    @functools.wraps(func)
    async def wrapper(self, *args, user_id: UUID | None = None, **kwargs):
        if not user_id:
            raise AuthError()
        return await func(self, *args, user_id=user_id, **kwargs)

    return wrapper
