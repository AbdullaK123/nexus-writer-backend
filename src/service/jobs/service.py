from typing import Optional, Callable, Any
from tortoise import Tortoise
from src.data.models import Job, Story
from src.data.models.enums import JobStatus
from src.infrastructure.ai.enums import JobType
from src.data.schemas.job import JobStatusResponse
from src.service.exceptions import ServiceError, NotFoundError
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
from datetime import datetime, timezone as tz
from functools import wraps

log = get_layer_logger(LAYER_SERVICE)


def get_now() -> datetime:
    return datetime.now(tz.utc)


async def get_job_status(job_id: str) -> JobStatusResponse:
    job = await Job.get_or_none(id=job_id)
    if job is None:
        raise NotFoundError("Job not found")
    return job.to_status_response()


async def queue_extraction_job(
    story_id: str,
    job_type: JobType,
    message: str = "",
    job_args: Optional[dict] = None
) -> JobStatusResponse:
    
    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")

    job = await Job.create(
        story_id=story_id,
        type=job_type,
        message=message,
        params=job_args or {}
    )

    return job.to_status_response()


async def claim_next_job(on_started_message: str = "") -> Optional[Job]:

    conn = Tortoise.get_connection("default")
    rows = await conn.execute_query_dict(
        """
        UPDATE job
        SET status = 'running', started_at = NOW(), message=$1
        WHERE id = (
            SELECT id
            FROM job
            WHERE status = 'queued'
            ORDER BY queued_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING *;
        """,
        [on_started_message]
    )
    if not rows:
        return None
    return await Job.get(id=rows[0]["id"])

    

async def mark_job_failed(job_id: str, message: str = "") -> Job:

    job = await Job.get_or_none(id=job_id)

    if job is None:
        raise NotFoundError("Job not found")
    
    if job.status not in (JobStatus.RUNNING, JobStatus.QUEUED):
        raise ServiceError("Only queued or running jobs can be marked as failed")
    
    job.status = JobStatus.FAILED
    job.failed_at = get_now()
    job.message = message

    await job.save(update_fields=["status", "failed_at", "message"])

    return job

async def mark_job_completed(job_id: str, message: str = "") -> Job:

    job = await Job.get_or_none(id=job_id)

    if job is None:
        raise NotFoundError("Job not found")
    
    if job.status != JobStatus.RUNNING:
        raise ServiceError("Only running jobs can be marked as complete")
    
    job.status = JobStatus.COMPLETED
    job.completed_at = get_now()
    job.message = message

    await job.save(update_fields=["status", "completed_at", "message"])

    return job


def poll_job_registry(
    job_name: str,
    on_started_message: str = "",
    on_failed_message: str = "",
    on_completed_message: str = ""
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:

            job = await claim_next_job(on_started_message)

            if job is None:
                return
            
            try:
                result = await func(**job.params) # type: ignore
                await mark_job_completed(job.id, on_completed_message)
                return result
            except Exception as e:
                await mark_job_failed(job.id, on_failed_message)
                log.error(f"{job_name}.failed", error=str(e))
        
        return wrapper
    
    return decorator

