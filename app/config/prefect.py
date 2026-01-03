"""
Prefect configuration for background task processing.
"""
import os
from prefect import get_client
from prefect.client.orchestration import PrefectClient
from app.config.settings import app_config
from typing import Optional


# Prefect settings - reads from PREFECT_API_URL environment variable automatically
# When set, flows will be submitted to the Prefect server instead of running locally
PREFECT_API_URL: Optional[str] = os.getenv("PREFECT_API_URL")

# Flow configuration defaults
DEFAULT_TASK_RETRIES = 3
DEFAULT_TASK_RETRY_DELAYS = [30, 60, 120]  # Exponential backoff in seconds
DEFAULT_FLOW_RETRIES = 2

# Circuit breaker settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30  # seconds
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS = 1

# Timeouts
EXTRACTION_TASK_TIMEOUT = 300  # 5 minutes per AI call
CHAPTER_FLOW_TIMEOUT = 600  # 10 minutes per chapter
CASCADE_FLOW_TIMEOUT = 7200  # 2 hours max for full cascade

# Result storage
RESULT_STORAGE_TTL = 86400  # 24 hours


async def get_prefect_client() -> PrefectClient:
    """Get async Prefect client for job management"""
    async with get_client() as client:
        return client
