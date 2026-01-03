"""
Jobs controller for background task management.

Endpoints for:
- Queuing extraction and line edit jobs
- Polling job status
- DLQ management (list, retry, resolve)
- Circuit breaker status and reset
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, Depends, HTTPException, status
from pydantic import BaseModel

from app.providers.jobs import JobProvider, get_job_provider
from app.providers.auth import get_current_user
from app.models import User, DLQStatus
from app.schemas.jobs import JobStatusResponse, JobQueuedResponse


job_controller = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)]
)


# === Job Status ===

@job_controller.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobStatusResponse:
    """
    Get detailed status of a background job with progress tracking.
    
    Poll this endpoint to track extraction progress in real-time.
    
    **Response includes:**
    - Current status (queued, progress, success, failure)
    - Progress details (current chapter, total chapters, percentage)
    - Estimated time remaining
    - Error information (if failed)
    """
    return await job_provider.get_job_status(job_id)


# === Queue Jobs ===

@job_controller.post("/line-edits/{chapter_id}", response_model=JobQueuedResponse)
async def queue_line_edit_job(
    chapter_id: str,
    force: bool = Query(
        False, 
        description="Force generation even if recently generated (within 24h)"
    ),
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobQueuedResponse:
    """
    Queue line edit generation for a chapter.
    
    **Process:**
    1. Generates surgical prose improvements using AI
    2. Returns structured line edits with before/after text
    
    **Validation:**
    - Checks if edits were generated within last 24 hours
    - Use `force=true` to override and regenerate
    """
    return await job_provider.queue_line_edit_job(
        chapter_id=chapter_id,
        user_id=current_user.id,
        force=force
    )


@job_controller.post("/extraction/{chapter_id}", response_model=JobQueuedResponse)
async def queue_cascade_extraction(
    chapter_id: str,
    force: bool = Query(
        False, 
        description="Force extraction even if word delta < 1000"
    ),
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobQueuedResponse:
    """
    Queue **cascade extraction** for a chapter and all subsequent chapters.
    
    **Resilient workflow with checkpointing:**
    - Each chapter is committed independently
    - Failures at chapter N preserve chapters 1 to N-1
    - Can resume from last successful chapter
    - Circuit breaker protects against API outages
    
    **What happens:**
    1. Re-extracts the edited chapter with accumulated context
    2. Re-extracts ALL chapters after it (rolling context propagates changes)
    3. Updates story-level data (character bios, plot threads, world bible, etc.)
    
    **Performance:**
    - ~60 seconds per chapter (4 parallel AI extractions + synthesis)
    - All 4 extractions run concurrently for each chapter
    - Progress tracked in real-time
    """
    return await job_provider.queue_extraction_job(
        user_id=current_user.id,
        chapter_id=chapter_id,
        force=force
    )


# === Dead-Letter Queue Management ===

class DLQJobSummary(BaseModel):
    """Summary of a DLQ job"""
    id: str
    flow_run_id: str
    flow_name: str
    error_type: str
    error_message: str
    failed_at: datetime
    status: DLQStatus
    chapter_id: Optional[str] = None
    story_id: Optional[str] = None


class DLQJobDetail(BaseModel):
    """Detailed DLQ job including input payload"""
    id: str
    flow_run_id: str
    flow_name: str
    task_name: Optional[str]
    chapter_id: Optional[str]
    story_id: Optional[str]
    user_id: str
    input_payload: dict
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    original_retry_count: int
    failed_at: datetime
    status: DLQStatus
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]


class DLQResolution(BaseModel):
    """Request body for resolving a DLQ job"""
    status: DLQStatus
    notes: Optional[str] = None


class BulkRetryRequest(BaseModel):
    """Request body for bulk DLQ retry"""
    flow_name: Optional[str] = None
    error_type: Optional[str] = None
    failed_after: Optional[datetime] = None


class BulkRetryResponse(BaseModel):
    """Response for bulk retry"""
    retried_count: int
    new_job_ids: List[str]


@job_controller.get("/dlq", response_model=List[DLQJobSummary])
async def list_dlq_jobs(
    status_filter: Optional[DLQStatus] = Query(
        None,
        alias="status",
        description="Filter by status (pending, retried, resolved, ignored)"
    ),
    flow_name: Optional[str] = Query(
        None,
        description="Filter by flow name (cascade-extraction, line-edits)"
    ),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> List[DLQJobSummary]:
    """
    List jobs in the dead-letter queue.
    
    Jobs end up here after exhausting all retries.
    Use this to monitor failed jobs and decide on retry/ignore.
    """
    jobs = await job_provider.get_dlq_jobs(
        status_filter=status_filter,
        flow_name=flow_name,
        limit=limit,
    )
    
    return [
        DLQJobSummary(
            id=j.id,
            flow_run_id=j.flow_run_id,
            flow_name=j.flow_name,
            error_type=j.error_type,
            error_message=j.error_message,
            failed_at=j.failed_at,
            status=j.status,
            chapter_id=j.chapter_id,
            story_id=j.story_id,
        )
        for j in jobs
    ]


@job_controller.get("/dlq/{dlq_id}", response_model=DLQJobDetail)
async def get_dlq_job(
    dlq_id: str,
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> DLQJobDetail:
    """
    Get full details of a DLQ job including input payload.
    
    Use this to inspect what went wrong and decide if retry is appropriate.
    """
    job = await job_provider.get_dlq_job(dlq_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ job not found"
        )
    
    return DLQJobDetail(
        id=job.id,
        flow_run_id=job.flow_run_id,
        flow_name=job.flow_name,
        task_name=job.task_name,
        chapter_id=job.chapter_id,
        story_id=job.story_id,
        user_id=job.user_id,
        input_payload=job.input_payload,
        error_type=job.error_type,
        error_message=job.error_message,
        stack_trace=job.stack_trace,
        original_retry_count=job.original_retry_count,
        failed_at=job.failed_at,
        status=job.status,
        resolved_at=job.resolved_at,
        resolved_by=job.resolved_by,
        resolution_notes=job.resolution_notes,
    )


@job_controller.post("/dlq/{dlq_id}/retry", response_model=JobQueuedResponse)
async def retry_dlq_job(
    dlq_id: str,
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobQueuedResponse:
    """
    Manually retry a single DLQ job.
    
    For cascade extractions, this will resume from the last successful chapter.
    """
    return await job_provider.resume_extraction_job(dlq_id, current_user.id)


@job_controller.post("/dlq/{dlq_id}/resolve", response_model=DLQJobDetail)
async def resolve_dlq_job(
    dlq_id: str,
    resolution: DLQResolution,
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> DLQJobDetail:
    """
    Mark a DLQ job as resolved or ignored.
    
    Use this when:
    - `resolved`: Issue was fixed manually or is no longer relevant
    - `ignored`: Known issue that doesn't need action
    """
    if resolution.status not in [DLQStatus.RESOLVED, DLQStatus.IGNORED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'resolved' or 'ignored'"
        )
    
    job = await job_provider.resolve_dlq_job(
        dlq_id=dlq_id,
        user_id=current_user.id,
        resolution_status=resolution.status,
        notes=resolution.notes,
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ job not found"
        )
    
    return DLQJobDetail(
        id=job.id,
        flow_run_id=job.flow_run_id,
        flow_name=job.flow_name,
        task_name=job.task_name,
        chapter_id=job.chapter_id,
        story_id=job.story_id,
        user_id=job.user_id,
        input_payload=job.input_payload,
        error_type=job.error_type,
        error_message=job.error_message,
        stack_trace=job.stack_trace,
        original_retry_count=job.original_retry_count,
        failed_at=job.failed_at,
        status=job.status,
        resolved_at=job.resolved_at,
        resolved_by=job.resolved_by,
        resolution_notes=job.resolution_notes,
    )


@job_controller.post("/dlq/bulk-retry", response_model=BulkRetryResponse)
async def bulk_retry_dlq(
    request: BulkRetryRequest,
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> BulkRetryResponse:
    """
    Bulk retry DLQ jobs matching criteria.
    
    Useful after an API outage is resolved - retry all failed jobs at once.
    
    **Filters (all optional):**
    - `flow_name`: Only retry specific flow type
    - `error_type`: Only retry specific error type
    - `failed_after`: Only retry jobs that failed after this time
    """
    new_job_ids = await job_provider.bulk_retry_dlq(
        user_id=current_user.id,
        flow_name=request.flow_name,
        error_type=request.error_type,
        failed_after=request.failed_after,
    )
    
    return BulkRetryResponse(
        retried_count=len(new_job_ids),
        new_job_ids=new_job_ids,
    )


# === Circuit Breaker Management ===

class CircuitBreakerStatusResponse(BaseModel):
    """Circuit breaker status"""
    name: str
    state: str  # closed, open, half_open
    failure_count: int
    last_failure_at: Optional[datetime]
    time_to_recovery: Optional[int]  # seconds


@job_controller.get("/circuit-breakers", response_model=List[CircuitBreakerStatusResponse])
async def get_circuit_breaker_status(
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> List[CircuitBreakerStatusResponse]:
    """
    Get status of all circuit breakers.
    
    Circuit breakers protect against cascading failures:
    - `gemini-api`: Protects AI extraction calls
    - `postgres`: Protects database operations
    
    **States:**
    - `closed`: Normal operation
    - `open`: Rejecting requests (API down)
    - `half_open`: Testing recovery
    """
    statuses = await job_provider.get_circuit_breakers()
    
    return [
        CircuitBreakerStatusResponse(
            name=s.name,
            state=s.state.value,
            failure_count=s.failure_count,
            last_failure_at=s.last_failure_at,
            time_to_recovery=s.time_to_recovery,
        )
        for s in statuses
    ]


@job_controller.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(
    name: str,
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> dict:
    """
    Manually reset a circuit breaker to CLOSED state.
    
    Use this after confirming the underlying service is healthy again.
    """
    success = await job_provider.reset_circuit_breaker(name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circuit breaker '{name}' not found"
        )
    
    return {"message": f"Circuit breaker '{name}' reset to CLOSED"}
