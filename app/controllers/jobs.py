"""
Jobs controller for background task management.

Endpoints for:
- Queuing extraction and line edit jobs
- Polling job status
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.jobs import JobService, get_job_service
from app.services.auth import get_current_user
from app.models import User
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
    job_service: JobService = Depends(get_job_service)
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
    return await job_service.get_job_status(job_id)


# === Queue Jobs ===

@job_controller.post("/line-edits/{chapter_id}", response_model=JobQueuedResponse)
async def queue_line_edit_job(
    chapter_id: str,
    force: bool = Query(
        False, 
        description="Force generation even if recently generated (within 24h)"
    ),
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
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
    return await job_service.queue_line_edit_job(
        chapter_id=chapter_id,
        user_id=current_user.id,
        force=force
    )


@job_controller.post("/extraction/{chapter_id}", response_model=JobQueuedResponse)
async def queue_extraction(
    chapter_id: str,
    force: bool = Query(
        False, 
        description="Force extraction even if word delta < 1000"
    ),
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> JobQueuedResponse:
    """
    Queue extraction for a single chapter.
    
    **Resilient workflow with checkpointing:**
    - Results are saved immediately after extraction
    
    **What happens:**
    1. Runs 4 parallel AI extractions (characters, plot, world, structure)
    2. Synthesizes results into condensed context
    3. Saves all extraction data to the chapter
    
    **Performance:**
    - ~60 seconds per chapter
    - All 4 extractions run concurrently
    - Progress tracked in real-time
    """
    return await job_service.queue_extraction_job(
        user_id=current_user.id,
        chapter_id=chapter_id,
        force=force
    )
