import functools
from openai import AuthenticationError, BadRequestError, NotFoundError, OpenAIError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.infrastructure.exceptions import DatabaseError
from src.infrastructure.exceptions import (
    LLMConfigError,
    LLMServiceError,
    InfrastructureError,
)
from src.infrastructure.config import config
from loguru import logger



def handle_db_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("infra.db_error", func=func.__qualname__, error=str(e))
            raise DatabaseError(str(e), original=e)

    return wrapper


def handle_openai_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except InfrastructureError as e:
            logger.error("infra.llm_error", func=func.__qualname__, error=str(e))
            raise  # already translated, pass through
        except (AuthenticationError, BadRequestError, NotFoundError) as e:
            logger.error("infra.llm_config_error", func=func.__qualname__, error=str(e))
            raise LLMConfigError(f"LLM Config Error: {e}", original=e) from e
        except OpenAIError as e:
            logger.error("infra.llm_service_error", func=func.__qualname__, error=str(e))
            raise LLMServiceError(
                f"LLM Provider failed after retries: {e}", original=e
            ) from e
        except Exception as e:
            logger.error("infra.llm_uncaught_error", func=func.__qualname__, error=str(e))
            raise LLMServiceError(
                f"LLM Provider failed after retries: {e}", original=e
            ) from e

    return wrapper


def retry_extraction(*exc_types: type[BaseException]):
    """Retry an LLM extraction call when its post-validation rejects the result.

    Used by extraction services whose validation layer raises an exception on
    model nondeterminism (e.g. non-verbatim quotes). Retry policy is sourced
    from `config.ai.extraction_retry_*` so it can be tuned without code changes.

    The exception types to retry on are passed by the caller, keeping
    infrastructure free of any upward import into the service layer.

    Usage:
        @retry_extraction(ValidationError)
        async def _extract_and_validate(...): ...
    """

    def _log_before_sleep(retry_state):
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.warning(
            "infra.extraction_retry",
            func=retry_state.fn.__qualname__ if retry_state.fn else None,
            attempt=retry_state.attempt_number,
            max_attempts=config.ai.extraction_retry_attempts,
            wait_seconds=config.ai.extraction_retry_wait_seconds,
            exc_type=type(exc).__name__ if exc else None,
            error=str(exc)[:500] if exc else None,
        )

    def _log_final_failure(retry_state):
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.error(
            "infra.extraction_retry_exhausted",
            func=retry_state.fn.__qualname__ if retry_state.fn else None,
            attempts=retry_state.attempt_number,
            exc_type=type(exc).__name__ if exc else None,
            error=str(exc)[:500] if exc else None,
        )
        if exc:
            raise exc

    def decorator(func):
        @retry(
            stop=stop_after_attempt(config.ai.extraction_retry_attempts),
            wait=wait_fixed(config.ai.extraction_retry_wait_seconds),
            retry=retry_if_exception_type(exc_types),
            before_sleep=_log_before_sleep,
            retry_error_callback=_log_final_failure,
        )
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator
