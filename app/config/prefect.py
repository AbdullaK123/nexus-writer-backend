"""
Prefect configuration for background task processing.
"""
from prefect import get_client
from prefect.client.orchestration import PrefectClient
from app.config.settings import app_config
from typing import Optional


# Prefect settings - reads from settings or PREFECT_API_URL environment variable
PREFECT_API_URL: Optional[str] = app_config.prefect_api_url

# Flow configuration defaults from settings
DEFAULT_TASK_RETRIES = app_config.default_task_retries
DEFAULT_TASK_RETRY_DELAYS = [
    float(app_config.default_task_retry_delay_1),
    float(app_config.default_task_retry_delay_2),
    float(app_config.default_task_retry_delay_3),
]  # Exponential backoff in seconds
DEFAULT_FLOW_RETRIES = app_config.default_flow_retries

# Timeouts
EXTRACTION_TASK_TIMEOUT = app_config.extraction_task_timeout
CHAPTER_FLOW_TIMEOUT = app_config.chapter_flow_timeout

# Result storage
RESULT_STORAGE_TTL = app_config.result_storage_ttl


async def get_prefect_client() -> PrefectClient:
    """Get async Prefect client for job management"""
    async with get_client() as client:
        return client
