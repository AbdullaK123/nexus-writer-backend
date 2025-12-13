from sqlmodel.ext.asyncio.session import AsyncSession
from celery import Celery
from celery.result import AsyncResult
from app.config.celery import celery_app
from fastapi import Depends, HTTPException, status
from app.ai.tasks import run_line_edit_job, run_context_extraction_job
from app.core.database import get_db
from app.schemas.jobs import (
    JobQueuedResponse, 
    JobStatus, 
    JobStatusResponse,
    ExtractionProgress
)
from app.providers.chapter import ChapterProvider
from app.providers.story import StoryProvider
from app.utils.decorators import log_errors
from app.utils.html import html_to_plain_text
from app.models import Story, Chapter
from loguru import logger
from datetime import datetime
from typing import Optional

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
        """Get detailed status of a job by ID with progress tracking"""
        result = AsyncResult(id=job_id, app=self.celery_app)

        # Map Celery states to our JobStatus enum
        status_map = {
            "PENDING": JobStatus.QUEUED,
            "STARTED": JobStatus.STARTING,
            "PROGRESS": JobStatus.PROGRESS,
            "SUCCESS": JobStatus.SUCCESS,
            "FAILURE": JobStatus.FAILURE,
            "RETRY": JobStatus.RETRY,
        }

        response = JobStatusResponse(
            job_id=job_id,
            status=status_map.get(result.state, JobStatus.PENDING)
        )

        # Handle different states with metadata
        if result.state == 'PENDING':
            response.status = JobStatus.QUEUED
            response.message = "Task queued, waiting to start"
        
        elif result.state == 'STARTING':
            response.status = JobStatus.STARTING
            response.message = "Initializing extraction pipeline"
            if isinstance(result.info, dict):
                response.started_at = result.info.get('started_at')
        
        elif result.state == 'PROGRESS':
            response.status = JobStatus.PROGRESS
            
            # Extract progress metadata from Celery task
            meta = result.info or {}
            if all(k in meta for k in ['current', 'total', 'chapter', 'percent']):
                response.progress = ExtractionProgress(
                    current=meta['current'],
                    total=meta['total'],
                    chapter=meta['chapter'],
                    percent=meta['percent']
                )
                response.message = (
                    f"Extracting Chapter {meta['chapter']} "
                    f"({meta['current']}/{meta['total']})"
                )
            else:
                response.message = "Processing..."
        
        elif result.state == 'SUCCESS':
            response.status = JobStatus.SUCCESS
            response.completed_at = datetime.utcnow()
            response.result = result.result
            
            # Create success message
            if isinstance(result.result, list):
                chapters_count = len(result.result)
                response.message = f"Successfully extracted {chapters_count} chapter{'s' if chapters_count != 1 else ''}!"
            else:
                response.message = "Extraction complete!"
        
        elif result.state == 'FAILURE':
            response.status = JobStatus.FAILURE
            response.completed_at = datetime.utcnow()
            
            # Extract error information
            if isinstance(result.info, dict):
                response.error = result.info.get('error', str(result.info))
                response.error_type = result.info.get('exc_type', 'Unknown')
            else:
                response.error = str(result.info)
            
            response.message = "Extraction failed"
        
        elif result.state == 'RETRY':
            response.status = JobStatus.RETRY
            if isinstance(result.info, dict):
                response.retry_count = result.info.get('retries', 0)
                response.max_retries = 3
                response.message = (
                    f"Retrying after error "
                    f"(attempt {response.retry_count + 1}/3)"
                )
            else:
                response.message = "Retrying..."

        return response

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
            time_since_generation = datetime.utcnow() - chapter.line_edits_generated_at
            
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
        
        # Get chapter number
        chapter_number = chapter.chapter_number
        
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
            started_at=datetime.utcnow(),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number
        )

    @log_errors
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
        force: bool = False
    ) -> JobQueuedResponse:
        """
        Queue cascade extraction for a chapter and all subsequent chapters.
        
        This will re-extract the edited chapter and all chapters after it
        to ensure rolling context propagates changes forward.
        """
        
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found!"
            )
        
        # Check if extraction needed (unless forced)
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
        
        # Get chapter number using the property
        chapter_number = chapter.chapter_number
        
        # Calculate how many chapters will be re-extracted
        # (current chapter + all chapters after it)
        total_chapters = len(story.path_array or [])
        chapters_to_extract = total_chapters - chapter_number + 1
        
        # Estimate duration (60 seconds per chapter)
        estimated_duration = chapters_to_extract * 60
        
        # Queue the cascade extraction task
        # Note: We only pass chapter_id and chapter_number now
        # The task itself queries the DB for chapter content
        result: AsyncResult = run_context_extraction_job.delay(
            chapter_id=chapter_id,
            chapter_number=chapter_number
        )

        logger.info(
            f"Queued cascade extraction for Chapter {chapter_number} "
            f"'{chapter.title}' - will re-extract {chapters_to_extract} chapters "
            f"(task_id: {result.id})"
        )

        return JobQueuedResponse(
            job_id=result.id,
            job_name=f"Cascade Extraction - Chapter {chapter_number}: {chapter.title}",
            started_at=datetime.utcnow(),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            chapters_to_extract=chapters_to_extract,
            estimated_duration_seconds=estimated_duration
        )
    

async def get_job_provider(
    db: AsyncSession = Depends(get_db)
) -> JobProvider:
    return JobProvider(celery_app=celery_app, db=db)