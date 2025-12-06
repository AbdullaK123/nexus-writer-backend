from sqlmodel.ext.asyncio.session import AsyncSession
from celery import Celery
from celery.result import AsyncResult
from app.config.celery import celery_app
from fastapi import HTTPException, status
from app.ai.tasks import run_line_edit_job, run_context_extraction_job
from app.schemas.jobs import JobQueuedResponse, JobStatus, JobStatusResponse
from app.providers.chapter import ChapterProvider
from app.utils.decorators import log_errors
from app.utils.html import get_preview_content
from app.models import Story
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


    @log_errors
    async def get_job_status(
        self,
        job_id
    ) -> JobStatusResponse:
        
        result = AsyncResult(id=job_id, app=self.celery_app)

        status_map = {
            "PENDING": JobStatus.PENDING,
            "SUCCESS": JobStatus.SUCCESS,
            "FAILURE": JobStatus.FAILURE,
            "STARTED": JobStatus.STARTED
        }

        return JobStatusResponse(
            job_id=job_id,
            status = status_map.get(result.status, status_map["PENDING"])
        )

    @log_errors
    async def queue_line_edit_job(
        self, 
        chapter_id: str,
        user_id: str,
        chapter_number: int,
        force: bool = False
    ) -> JobQueuedResponse:

        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        if not force and not chapter.needs_extraction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chapter does not need extraction"
            )
        
        story = await self.db.get(Story, chapter.story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!"
            )
        
        result: AsyncResult = run_line_edit_job.delay(
            chapter_id = chapter.id,
            story_context = story.story_context,
            current_chapter_content = get_preview_content(chapter.content),
            chapter_number = chapter_number,
            chapter_title = chapter.title
        )

        logger.info(f"Queued line edit job for Chapter {chapter_number} with id: {chapter_id}")

        return JobQueuedResponse(
            job_id = result.id,
            job_name = f"Chapter {chapter_id} line edit",
            started_at = datetime.now(),
            status = JobStatus.PENDING
        )

    @log_errors
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
        chapter_number: int
    ) -> JobQueuedResponse:
        
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found!"
            )
        
        story = await self.db.get(Story, chapter.story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!"
            )
        
        result: AsyncResult = run_context_extraction_job.delay(
            chapter_id=chapter_id,
            chapter_number = chapter_number,
            chapter_title = chapter.title,
            story_context = story.story_context,
            current_chapter_content = get_preview_content(chapter.content),
            word_count = chapter.word_count
        ) 

        logger.info(f"Queued extraction job for Chapter {chapter_number} with id: {chapter_id}")

        return JobQueuedResponse(
            job_id=result.id,
            job_name=f"Chapter {chapter_number} extraction",
            started_at=datetime.now(),
            status = JobStatus.PENDING
        )



