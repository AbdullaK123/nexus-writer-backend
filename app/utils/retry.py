"""Reusable tenacity retry decorators for external service boundaries."""

import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
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

_log = logging.getLogger("app.retry")

# ── LLM / Google Gemini ─────────────────────────────────────────────────────
# Retries transient Google API errors and HTTP-level connection failures.
# SDK-level max_retries handles simple 429/503; this covers broader outages.

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
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)

# ── MongoDB ──────────────────────────────────────────────────────────────────
# Retries transient connection / network errors from the async pymongo driver.

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
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)

# ── Redis ────────────────────────────────────────────────────────────────────
# Retries transient connection / loading errors from the sync Redis client.

_REDIS_RETRYABLE = (
    RedisConnectionError,
    RedisTimeoutError,
    BusyLoadingError,
)

retry_redis = retry(
    retry=retry_if_exception_type(_REDIS_RETRYABLE),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)

# ── Network (DuckDB / MotherDuck / Prefect) ──────────────────────────────────
# Retries general connection / timeout errors for HTTP-based external services.

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
    before_sleep=before_sleep_log(_log, logging.WARNING),
    reraise=True,
)
