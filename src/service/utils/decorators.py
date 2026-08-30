import functools
from uuid import UUID
from src.data.exceptions import NotFoundError as DataNotFound, DuplicateError
from src.infrastructure.exceptions import DatabaseError, LLMConfigError, LLMServiceError, InfrastructureError
from src.service.exceptions import (
    InternalError,
    ServiceError,
    NotFoundError,
    ConflictError,
    AuthError,
)
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)


TRANSIENT_QUEUE_ERRORS = (
    ConnectionError,
    TimeoutError,
    RedisConnectionError,
    RedisTimeoutError,
)


def _on_enqueue_retries_exhausted(retry_state):
    error = retry_state.outcome.exception() if retry_state.outcome else None
    logger.error(
        "queue.enqueue_retries_exhausted",
        attempts=retry_state.attempt_number,
        error=str(error) if error else None,
    )
    return None


retry_enqueue = retry(
    retry=retry_if_exception_type(TRANSIENT_QUEUE_ERRORS),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(
        initial=0.5,
        max=5,
    ),
    retry_error_callback=_on_enqueue_retries_exhausted,
    reraise=True,
)


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
                "service.infrastructure_failure",
                func=func.__qualname__,
                error=str(e.original),
            )
            raise InternalError("A database error occurred")
        except LLMServiceError as e:
            logger.error(
                "service.infrastructure_failure",
                func=func.__qualname__,
                error=str(e.original)
            )
            raise InternalError("LLM service failure occurred")
        except LLMConfigError as e:
            logger.error(
                "service.infrastructure_failure",
                func=func.__qualname__,
                error=str(e.original)
            )
            raise InternalError("LLM config failure occurred")
        except InfrastructureError as e:
            logger.error(
                "service.infrastructure_failure",
                func=func.__qualname__,
                error=str(e)
            )
            raise InternalError("Uncaught infrastructure failure.")

    return wrapper


def handle_service_errors_stream(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            async for item in func(*args, **kwargs):
                yield item
        except ServiceError:
            raise
        except DataNotFound as e:
            raise NotFoundError(f"{e.entity} not found")
        except DuplicateError as e:
            raise ConflictError(f"{e.entity} with this {e.field} already exists")
        except DatabaseError as e:
            logger.error(
                "service.infrastructure_failure",
                func=func.__qualname__,
                error=str(e.original),
            )
            raise ServiceError("A database error occurred")

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
