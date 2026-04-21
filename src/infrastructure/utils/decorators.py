import functools
from openai import AuthenticationError, BadRequestError, NotFoundError, OpenAIError
from src.infrastructure.exceptions import DatabaseError
from src.infrastructure.exceptions import (
    LLMConfigError,
    LLMServiceError,
    InfrastructureError,
)
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
