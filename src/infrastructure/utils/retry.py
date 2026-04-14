"""Reusable tenacity retry decorators for external service boundaries."""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from google.api_core.exceptions import (
    DeadlineExceeded,
    InternalServerError,
    ResourceExhausted,
    ServiceUnavailable,
)
from httpx import ConnectError, ReadTimeout
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    NetworkTimeout,
    ServerSelectionTimeoutError,
)
from redis.exceptions import (
    BusyLoadingError,
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)
from src.shared.utils.logging_context import get_layer_logger, LAYER_INFRA

log = get_layer_logger(LAYER_INFRA)


def _before_sleep_loguru(category: str):
    """Create a tenacity before_sleep callback that logs retries via loguru."""
    def _log_retry(retry_state):
        exception = retry_state.outcome.exception()
        log.warning(
            "retry.attempt",
            category=category,
            fn=retry_state.fn.__qualname__,
            attempt=retry_state.attempt_number,
            wait_s=round(getattr(retry_state.next_action, "sleep", 0), 2),
            error_type=type(exception).__name__,
            error=str(exception),
        )
    return _log_retry


# ── LLM / Google Gemini ─────────────────────────────────────────────────────
_LLM_RETRYABLE = (
    ServiceUnavailable,
    ResourceExhausted,
    DeadlineExceeded,
    InternalServerError,
    ConnectError,
    ReadTimeout,
    ConnectionError,
    TimeoutError,
)

retry_llm = retry(
    retry=retry_if_exception_type(_LLM_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    before_sleep=_before_sleep_loguru("llm"),
    reraise=True,
)

# ── MongoDB ──────────────────────────────────────────────────────────────────
_MONGO_RETRYABLE = (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    AutoReconnect,
    NetworkTimeout,
)

retry_mongo = retry(
    retry=retry_if_exception_type(_MONGO_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=_before_sleep_loguru("mongo"),
    reraise=True,
)

# ── Redis ────────────────────────────────────────────────────────────────────
_REDIS_RETRYABLE = (
    RedisConnectionError,
    RedisTimeoutError,
    BusyLoadingError,
)

retry_redis = retry(
    retry=retry_if_exception_type(_REDIS_RETRYABLE),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    before_sleep=_before_sleep_loguru("redis"),
    reraise=True,
)

# ── Network (DuckDB / MotherDuck / Prefect) ──────────────────────────────────
_NETWORK_RETRYABLE = (
    ConnectError,
    ReadTimeout,
    ConnectionError,
    TimeoutError,
    OSError,
)

retry_network = retry(
    retry=retry_if_exception_type(_NETWORK_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    before_sleep=_before_sleep_loguru("network"),
    reraise=True,
)
