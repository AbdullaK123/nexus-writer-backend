from sqlmodel.ext.asyncio.session import AsyncSession
from celery import Celery
from celery.result import AsyncResult
from app.config.celery import celery_app
from fastapi import Depends, HTTPException, status
from app.ai.tasks import run_line_edit_job, run_context_extraction_job
from app.core.database import get_db
from app.schemas.jobs import JobQueuedResponse, JobStatus, JobStatusResponse
from app.providers.chapter import ChapterProvider
from app.providers.story import StoryProvider
from app.utils.decorators import log_errors
from app.utils.html import html_to_plain_text
from app.models import Story, Chapter
from loguru import logger
from datetime import datetime

class JobProvider:

    def __init__(
        self, 
        celery_app: Celery,
        db: AsyncSession
    ):
        self.celery_app = celery_app
        self.db = db
        self.chapter_provider = ChapterProvider(db)
        self.story_provider = StoryProvider(db)


    @log_errors
    async def get_job_status(
        self,
        job_id: str
    ) -> JobStatusResponse:
        """Get status of a job by ID"""
        result = AsyncResult(id=job_id, app=self.celery_app)

        status_map = {
            "PENDING": JobStatus.PENDING,
            "SUCCESS": JobStatus.SUCCESS,
            "FAILURE": JobStatus.FAILURE,
            "STARTED": JobStatus.STARTED,
            "RETRY": JobStatus.PENDING,
            "PROGRESS": JobStatus.STARTED,
        }

        return JobStatusResponse(
            job_id=job_id,
            status=status_map.get(result.status, JobStatus.PENDING)
        )

    @log_errors
    async def queue_line_edit_job(
        self, 
        chapter_id: str,
        user_id: str,
        force: bool = False
    ) -> JobQueuedResponse:
        """Queue line edit generation for a chapter"""
        
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        # Check if line edits were recently generated
        if not force and chapter.line_edits_generated_at:
            from datetime import timedelta
            time_since_generation = datetime.now() - chapter.line_edits_generated_at
            
            if time_since_generation < timedelta(hours=24):
                hours_ago = time_since_generation.seconds // 3600
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Line edits generated {hours_ago}h ago. Use force=true to regenerate."
                )
        
        story = await self.db.get(Story, chapter.story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!"
            )
        
        # Calculate chapter number by getting ordered chapters
        chapters = await self.story_provider.get_ordered_chapters(user_id, story.id)
        chapter_number = next(
            (idx + 1 for idx, ch in enumerate(chapters) if ch.id == chapter_id),
            None
        )
        
        if chapter_number is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not determine chapter number"
            )
        
        # Queue task with HTML content (task will convert to plain text)
        result: AsyncResult = run_line_edit_job.delay(
            chapter_id=chapter.id,
            story_context=story.story_context,
            current_chapter_html=chapter.content,
            chapter_number=chapter_number, 
            chapter_title=chapter.title
        )

        logger.info(
            f"Queued line edit job for Chapter {chapter_number} "
            f"'{chapter.title}' (task_id: {result.id})"
        )

        return JobQueuedResponse(
            job_id=result.id,
            job_name=f"Line Edits - Chapter {chapter_number}: {chapter.title}",
            started_at=datetime.now(),
            status=JobStatus.PENDING
        )

    @log_errors
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
        force: bool = False
    ) -> JobQueuedResponse:
        """Queue context extraction for a chapter"""
        
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found!"
            )
        
        # Check if extraction needed
        if not force and not chapter.needs_extraction:
            word_delta = abs(chapter.word_count - (chapter.last_extracted_word_count or 0))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chapter doesn't need extraction (word delta: {word_delta} < 1000). Use force=true to override."
            )
        
        story = await self.db.get(Story, chapter.story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!"
            )
        
        # Calculate chapter number by getting ordered chapters
        chapters = await self.story_provider.get_ordered_chapters(user_id, story.id)
        chapter_number = next(
            (idx + 1 for idx, ch in enumerate(chapters) if ch.id == chapter_id),
            None
        )
        
        if chapter_number is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not determine chapter number"
            )
        
        # Convert HTML to plain text for extraction
        plain_text = html_to_plain_text(chapter.content)
        
        result: AsyncResult = run_context_extraction_job.delay(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            story_context=story.story_context,
            current_chapter_content=plain_text,
            word_count=chapter.word_count
        ) 

        logger.info(
            f"Queued extraction job for Chapter {chapter_number} "
            f"'{chapter.title}' (task_id: {result.id})"
        )

        return JobQueuedResponse(
            job_id=result.id,
            job_name=f"Extract Chapter {chapter_number}: {chapter.title}",
            started_at=datetime.now(),
            status=JobStatus.PENDING
        )
    

async def get_job_provider(
    db: AsyncSession = Depends(get_db)
) -> JobProvider:
    return JobProvider(celery_app=celery_app, db=db)