"""
Job service for managing background tasks via arq + JobRegistry.

Handles:
- Queuing new extraction and line edit jobs
- Polling job status
- Cancelling active jobs
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import uuid4

from arq.connections import ArqRedis
from arq.jobs import Job

from src.service.exceptions import NotFoundError, ValidationError
from src.infrastructure.redis.job_registry import JobRegistry, RegistryStatus
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

from src.data.models import Story, Chapter
from src.data.schemas.jobs import (
    JobQueuedResponse,
    JobStatus,
    JobStatusResponse,
    JobType,
)
from src.shared.utils.decorators import log_errors
from src.infrastructure.utils.retry import retry_network, retry_mongo
from pymongo.asynchronous.database import AsyncDatabase
from src.shared.utils.html import html_to_plain_text
from src.infrastructure.config import settings, config


# Map registry statuses to our JobStatus enum
_STATUS_MAP = {
    RegistryStatus.QUEUED: JobStatus.QUEUED,
    RegistryStatus.RUNNING: JobStatus.PROGRESS,
    RegistryStatus.COMPLETE: JobStatus.SUCCESS,
    RegistryStatus.FAILED: JobStatus.FAILURE,
    RegistryStatus.CANCELLED: JobStatus.FAILURE,
}


class JobService:
    """Service for job management operations"""

    def __init__(self, mongodb: AsyncDatabase, arq_pool: ArqRedis, registry: JobRegistry):
        self.mongodb = mongodb
        self._arq_pool = arq_pool
        self._registry = registry

    @log_errors
    async def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Get detailed status of a job by ID"""
        meta = await self._registry.get_meta(job_id)
        if not meta:
            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                message="Job not found or expired",
            )

        status_str = meta.get("status", "queued")
        try:
            reg_status = RegistryStatus(status_str)
        except ValueError:
            reg_status = RegistryStatus.QUEUED
        job_status = _STATUS_MAP.get(reg_status, JobStatus.PENDING)

        response = JobStatusResponse(
            job_id=job_id,
            status=job_status,
            queued_at=datetime.fromisoformat(meta["created_at"]) if meta.get("created_at") else None,
            started_at=datetime.fromisoformat(meta["started_at"]) if meta.get("started_at") else None,
            completed_at=datetime.fromisoformat(meta["completed_at"]) if meta.get("completed_at") else None,
        )

        if reg_status == RegistryStatus.RUNNING:
            response.message = "Processing..."
        elif reg_status == RegistryStatus.COMPLETE:
            response.message = "Task complete!"
        elif reg_status == RegistryStatus.FAILED:
            response.message = "Task failed"
            response.error = meta.get("error")
        elif reg_status == RegistryStatus.QUEUED:
            response.message = "Task queued, waiting to start"
        elif reg_status == RegistryStatus.CANCELLED:
            response.message = "Task cancelled"

        return response
        
    @log_errors
    async def cancel_all_jobs(
        self,
        chapter_id: Optional[str] = None,
        story_id: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> dict:
        if chapter_id is None and story_id is None:
            log.info("job.cancel_skipped: no filters provided")
            return {"jobs_cancelled": 0}

        tag_filter = [f"story:{story_id}"] if story_id else [f"chapter:{chapter_id}"]
        if job_type:
            tag_filter.append(job_type)

        active_jobs = await self._registry.find_by_tags(
            tag_filter,
            statuses=[RegistryStatus.QUEUED, RegistryStatus.RUNNING],
        )

        cancelled = 0
        for job_id in active_jobs:
            try:
                job = Job(job_id, self._arq_pool)
                await job.abort()
                await self._registry.set_status(job_id, RegistryStatus.CANCELLED)
                cancelled += 1
                log.info("job.cancelled", job_id=job_id, chapter_id=chapter_id, story_id=story_id)
            except Exception as e:
                log.warning("job.cancel_failed", job_id=job_id, error=str(e))

        return {
            "chapter_id": chapter_id,
            "jobs_cancelled": cancelled,
            "job_type": job_type if job_type else "line-edit, extraction, and reextraction"
        }
        
    @retry_mongo
    @log_errors
    async def _build_accumulated_context(
        self,
        story_id: str,
        chapter_number: int
    ) -> str:
        chapter_contexts = await self.mongodb.chapter_contexts.find(
            {
                "story_id": story_id, 
                "chapter_number": {"$lt": chapter_number}
            }
        ).to_list(length=None)
        contexts = [
            context["condensed_text"]
            for context in chapter_contexts
        ]
        return "\n\n".join(contexts)


    @retry_network
    @log_errors
    async def queue_line_edit_job(
        self,
        chapter_id: str,
        user_id: str,
        force: bool = False,
    ) -> JobQueuedResponse:
        """Queue line edit generation for a chapter"""
        chapter = await Chapter.get_or_none(id=chapter_id, user_id=user_id)
        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        # cancel all line edit jobs first
        cancel_result = await self.cancel_all_jobs(chapter_id=chapter_id, job_type="line-edit")

        if cancel_result.get("jobs_cancelled", 0) > 0:
            log.info(
                "job.cancelled_existing",
                jobs_cancelled=cancel_result['jobs_cancelled'],
                job_type=cancel_result['job_type'],
                chapter_id=chapter_id,
            )

        # Check MongoDB for line edit status
        chapter_edits = await self.mongodb.chapter_edits.find_one({"chapter_id": chapter_id})
        is_stale = chapter_edits.get("is_stale", False) if chapter_edits else False
        last_generated_at = chapter_edits.get("last_generated_at") if chapter_edits else None
        
        # Check if line edits were recently generated
        # Skip the check if edits are stale (content changed) or force flag is set
        if not force and not is_stale and last_generated_at:
            time_since = datetime.now(timezone.utc) - last_generated_at
            if time_since < timedelta(hours=config.jobs.line_edits_cooldown_hours):
                hours_ago = time_since.seconds // 3600
                raise ValidationError(
                    message=f"Line edits were generated {hours_ago}h ago. Click 'Regenerate' to get fresh edits.",
                )
        
        # Log if we're regenerating due to stale edits
        if is_stale:
            log.info("job.line_edits_stale", chapter_id=chapter_id)

        story = await Story.get_or_none(id=chapter.story_id)  # type: ignore[attr-defined]
        if not story:
            raise NotFoundError("We couldn't find the story this chapter belongs to.")

        chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)

        accumulated_context = await self._build_accumulated_context(
            chapter.story_id,  # type: ignore[attr-defined]
            Chapter.get_chapter_number(chapter.id, story.path_array)
        )

        # Submit to arq (runs on worker container)
        job_id = str(uuid4())
        tags = [f"chapter:{chapter_id}", f"story:{story.id}", "line-edits"]
        await self._registry.register(job_id, tags)
        await self._arq_pool.enqueue_job(
            "line_edits_job",
            _job_id=job_id,
            story_id=story.id,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            story_context=accumulated_context or "",
            story_path_array=story.path_array,
            chapter_content=chapter.content,
            user_id=user_id,
        )

        log.info(
            "job.line_edit_queued",
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            chapter_id=chapter_id,
            job_id=job_id,
        )

        return JobQueuedResponse(
            job_id=job_id,
            job_name=f"Line Edits - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.LINE_EDIT,
            started_at=datetime.now(timezone.utc),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=config.jobs.estimated_extraction_duration_seconds,
        )

    @retry_network
    @log_errors
    async def queue_reextraction_job(
        self,
        deleted_chapter_id: str,
        story_id: str,
        chapter_ids: List[str],
        user_id: str = "",
    ) -> JobQueuedResponse:
        """Queue a reextraction job after chapter deletion"""

        cancel_result = await self.cancel_all_jobs(story_id=story_id, job_type="reextraction")

        if cancel_result.get("jobs_cancelled", 0) > 0:
            log.info(
                "job.cancelled_existing",
                jobs_cancelled=cancel_result['jobs_cancelled'],
                job_type=cancel_result['job_type'],
                story_id=story_id,
            )

        job_id = str(uuid4())
        tags = [*[f"chapter:{cid}" for cid in chapter_ids], f"story:{story_id}", "reextraction"]
        await self._registry.register(job_id, tags)
        await self._arq_pool.enqueue_job(
            "reextract_chapters",
            _job_id=job_id,
            story_id=story_id,
            chapter_ids=chapter_ids,
            user_id=user_id,
        )

        log.info("job.reextraction_queued", chapter_ids=chapter_ids, story_id=story_id, job_id=job_id)

        return JobQueuedResponse(
            job_id=job_id,
            job_name=f"Reextraction after chapter: {deleted_chapter_id} deletion",
            job_type=JobType.REEXTRACTION,
            started_at=datetime.now(timezone.utc)
        )

    @retry_network
    @log_errors
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
    ) -> JobQueuedResponse:
        """Queue extraction for a single chapter"""
        chapter = await Chapter.get_or_none(id=chapter_id, user_id=user_id)
        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        # Cancel existing extraction jobs for this chapter
        cancel_result = await self.cancel_all_jobs(chapter_id=chapter_id, job_type="extraction")

        if cancel_result.get("jobs_cancelled", 0) > 0:
            log.info(
                "job.cancelled_existing",
                jobs_cancelled=cancel_result['jobs_cancelled'],
                job_type=cancel_result['job_type'],
                chapter_id=chapter_id,
            )
            
        story = await Story.get_or_none(id=chapter.story_id)  # type: ignore[attr-defined]
        if not story:
            raise NotFoundError("We couldn't find the story this chapter belongs to.")

        chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)

        # Submit to arq (runs on worker container)
        # Predecessor waiting and context building happen inside the job
        job_id = str(uuid4())
        tags = [f"chapter:{chapter_id}", f"story:{story.id}", "extraction"]
        await self._registry.register(job_id, tags)
        await self._arq_pool.enqueue_job(
            "extract_single_chapter",
            _job_id=job_id,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            word_count=chapter.word_count,
            story_id=story.id,
            story_path_array=story.path_array,
            content=html_to_plain_text(chapter.content),
            user_id=user_id,
        )

        log.info(
            "job.extraction_queued",
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            chapter_id=chapter_id,
            job_id=job_id,
        )

        return JobQueuedResponse(
            job_id=job_id,
            job_name=f"Extraction - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.EXTRACTION,
            started_at=datetime.now(timezone.utc),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=config.jobs.estimated_extraction_duration_seconds,
        )


