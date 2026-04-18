import functools
from openai import AuthenticationError, BadRequestError, NotFoundError, OpenAIError
from src.infrastructure.exceptions import DatabaseError
from src.shared.utils.logging_context import get_layer_logger, LAYER_INFRA
from src.infrastructure.exceptions import LLMConfigError, LLMServiceError, InfrastructureError

log = get_layer_logger(LAYER_INFRA)


def handle_db_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError:
            raise
        except Exception as e:
            log.error("infra.db_error", func=func.__qualname__, error=str(e))
            raise DatabaseError(str(e), original=e)

    return wrapper


def handle_openai_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except InfrastructureError as e:
            log.error("infra.llm_eror", func=func.__qualname__, error=str(e))
            raise  # already translated, pass through
        except (AuthenticationError, BadRequestError, NotFoundError) as e:
            log.error("infra.llm_config_error", func=func.__qualname__, error=str(e))
            raise LLMConfigError(f"LLM Config Error: {e}", original=e) from e
        except OpenAIError as e:
            log.error("infra.llm_service_error", func=func.__qualname__, error=str(e))
            raise LLMServiceError(f"LLM Provider failed after retries: {e}", original=e) from e
        except Exception as e:
            log.error("infra.llm_uncaught_error", func=func.__qualname__, error=str(e))
            raise LLMServiceError(f"LLM Provider failed after retries: {e}", original=e) from e
    return wrapper

