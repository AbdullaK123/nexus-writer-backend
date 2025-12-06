from fastapi import APIRouter, Query, Depends
from app.providers.jobs import JobProvider, get_job_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.jobs import JobStatusResponse, JobQueuedResponse


job_controller = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)]  # ← All routes require auth
)


@job_controller.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobStatusResponse:
    """
    Get status of a background job.
    
    Poll this endpoint to track job progress.
    """
    return await job_provider.get_job_status(job_id)


@job_controller.post("/line-edits/{chapter_id}", response_model=JobQueuedResponse)
async def queue_line_edit_job(
    chapter_id: str,
    force: bool = Query(False, description="Force generation even if recently generated"),
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobQueuedResponse:
    """
    Queue line edit generation for a chapter.
    
    - Checks if edits were generated within last 24 hours (unless force=true)
    - Converts TipTap HTML to plain text
    - Generates surgical prose improvements
    """
    return await job_provider.queue_line_edit_job(
        chapter_id=chapter_id,
        user_id=current_user.id,
        force=force
    )


@job_controller.post("/extraction/{chapter_id}", response_model=JobQueuedResponse)
async def queue_extraction_job(
    chapter_id: str,
    force: bool = Query(False, description="Force extraction even if not needed"),
    current_user: User = Depends(get_current_user),
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobQueuedResponse:
    """
    Queue context extraction for a chapter.
    
    - Checks if chapter needs extraction (word delta >= 1000)
    - Runs 4 parallel extractions (character, plot, world, structure)
    - Synthesizes condensed context
    - Updates story_context in Story table
    """
    return await job_provider.queue_extraction_job(
        user_id=current_user.id,
        chapter_id=chapter_id,
        force=force
    )