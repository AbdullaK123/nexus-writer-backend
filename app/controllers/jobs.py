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


@job_controller.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_provider: JobProvider = Depends(get_job_provider)
) -> JobStatusResponse:
    """
    Get detailed status of a background job with progress tracking.
    
    Poll this endpoint to track extraction progress in real-time.
    
    **Response includes:**
    - Current status (queued, starting, progress, success, failure, retry)
    - Progress details (current chapter, total chapters, percentage)
    - Estimated time remaining
    - Error information (if failed)
    - Retry information (if retrying)
    
    **Example usage:**
```javascript
    const interval = setInterval(async () => {
        const status = await fetch('/jobs/{job_id}');
        const data = await status.json();
        
        if (data.status === 'progress') {
            updateProgressBar(data.progress.percent);
            updateMessage(data.message);
        }
        
        if (data.is_terminal) {
            clearInterval(interval);
            showResult(data);
        }
    }, 2000);
```
    """
    return await job_provider.get_job_status(job_id)


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
    1. Converts TipTap HTML to plain text
    2. Generates surgical prose improvements using AI
    3. Returns structured line edits with before/after text
    
    **Validation:**
    - Checks if edits were generated within last 24 hours
    - Use `force=true` to override and regenerate
    
    **Returns:**
    - `job_id`: Use this to poll job status via `GET /jobs/{job_id}`
    - `estimated_duration_seconds`: Typically 30-60 seconds
    
    **Example:**
```bash
    POST /jobs/line-edits/abc123?force=true
```
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
    
    **What happens:**
    1. Re-extracts the edited chapter with accumulated context
    2. Re-extracts ALL chapters after it (rolling context propagates changes)
    3. Updates story-level data (character bios, plot threads, world bible, etc.)
    
    **Why cascade?**
    - Editing Chapter 15 changes the context for Chapters 16-32
    - All subsequent chapters need re-extraction to stay consistent
    - Example: Character dies in Ch. 15 → Chs. 16-32 reflect this
    
    **Process per chapter (runs sequentially):**
    1. 4 parallel extractions (character, plot, world, structure) - ~30s
    2. Synthesize condensed context - ~5s
    3. Save to database (flush)
    4. Rebuild accumulated context with TOON compression
    5. Repeat for next chapter
    
    **After all chapters:**
    1. 5 parallel story-level extractions - ~30s:
       - Character bios
       - Plot threads
       - World bible
       - Pacing & structure analysis
       - Story timeline
    2. Atomic commit (all or nothing)
    
    **Validation:**
    - Checks if word delta >= 1000 (unless `force=true`)
    - Use `force=true` to override and extract anyway
    
    **Performance:**
    - Time: ~60 seconds per chapter
    - 18 chapters = ~18 minutes total
    - Background processing (user doesn't wait)
    - Progress tracked in real-time
    
    **Returns:**
    - `job_id`: Poll via `GET /jobs/{job_id}` for progress
    - `chapters_to_extract`: How many chapters will be re-extracted
    - `estimated_duration_seconds`: Expected completion time
    
    **Example:**
```bash
    # Edit Chapter 15 in a 32-chapter book
    POST /jobs/extraction/abc123
    
    # Response:
    {
        "job_id": "xyz789",
        "chapters_to_extract": 18,
        "estimated_duration_seconds": 1080,
        "message": "Will re-extract Chapters 15-32"
    }
    
    # Poll for progress:
    GET /jobs/xyz789
    
    # Progress response:
    {
        "status": "progress",
        "progress": {
            "current": 8,
            "total": 18,
            "chapter": 22,
            "percent": 44
        },
        "message": "Extracting Chapter 22 (8/18)",
        "estimated_time_remaining": 600
    }
```
    
    **Important:**
    - This is a long-running task (minutes to tens of minutes)
    - User gets immediate response and can continue working
    - Poll job status for progress updates
    - Everything is atomic - either all chapters succeed or none do
    """
    return await job_provider.queue_extraction_job(
        user_id=current_user.id,
        chapter_id=chapter_id,
        force=force
    )