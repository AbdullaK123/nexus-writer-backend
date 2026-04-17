"""
Jobs controller for background task management.

Endpoints for:
- Queuing extraction and line edit jobs
- Polling job events
"""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse


from src.service.jobs.event_service import JobEventService
from src.service.jobs.service import JobService
from src.app.dependencies import get_current_user, get_job_event_service, get_job_service
from src.data.models import User
from src.data.schemas.jobs import JobQueuedResponse


job_controller = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)]
)


# === Job Events ===

@job_controller.get("/events/")
async def poll_job_events(
    user: User = Depends(get_current_user),
    job_event_service: JobEventService = Depends(get_job_event_service)
) -> JSONResponse:
    """Drain all pending events for the current user and return them as a JSON array."""
    events = await job_event_service.drain(user_id=user.id)
    return JSONResponse(content=[e.model_dump(mode="json") for e in events])

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
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> JobQueuedResponse:
    """
    Queue extraction for a single chapter.
    
    Runs 4 parallel AI extractions (characters, plot, world, structure),
    synthesizes results into condensed context, and saves to the chapter.
    ~60 seconds per chapter.
    """
    return await job_service.queue_extraction_job(
        user_id=current_user.id,
        chapter_id=chapter_id,
    )
