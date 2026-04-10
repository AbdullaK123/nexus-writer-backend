"""Prefect configuration for background task processing."""

from prefect import get_client
from prefect.client.orchestration import PrefectClient

from src.infrastructure.config.settings import settings, config

# Prefect settings
PREFECT_API_URL: str | None = settings.prefect_api_url

# Flow configuration defaults
DEFAULT_TASK_RETRIES = config.prefect.task_retries
DEFAULT_TASK_RETRY_DELAY = config.prefect.task_retry_delay

# Timeouts
EXTRACTION_TASK_TIMEOUT = config.prefect.extraction_task_timeout
CHAPTER_FLOW_TIMEOUT = config.prefect.chapter_flow_timeout

# Result storage
RESULT_STORAGE_TTL = config.prefect.result_storage_ttl


async def get_prefect_client() -> PrefectClient:
    """Get async Prefect client for job management"""
    async with get_client() as client:
        return client
