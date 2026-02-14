"""
Job service for managing background tasks via Prefect.

Handles:
- Queuing new extraction and line edit jobs
- Polling job status
"""
from datetime import datetime, timedelta
from typing import Optional, List, Any, cast
from uuid import UUID

from fastapi import Depends, HTTPException, status
from prefect import get_client
from prefect.client.schemas.objects import StateType, FlowRun
from prefect.client.schemas.filters import FlowRunFilter, FlowRunFilterTags, FlowRunFilterState, FlowRunFilterStateType
from prefect.client.orchestration import PrefectClient
from prefect.states import Cancelled
from prefect.deployments import run_deployment
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.models import Story, Chapter
from app.schemas.jobs import (
    JobQueuedResponse,
    JobStatus,
    JobStatusResponse,
    ExtractionProgress,
    JobType,
)
from app.services.chapter import ChapterService
from app.services.story import StoryService
from app.utils.decorators import log_errors
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.mongodb import get_mongodb


# Map Prefect states to our JobStatus enum
STATE_TYPE_MAP = {
    StateType.SCHEDULED: JobStatus.QUEUED,
    StateType.PENDING: JobStatus.QUEUED,
    StateType.RUNNING: JobStatus.PROGRESS,
    StateType.COMPLETED: JobStatus.SUCCESS,
    StateType.FAILED: JobStatus.FAILURE,
    StateType.CANCELLED: JobStatus.FAILURE,
    StateType.CANCELLING: JobStatus.PROGRESS,
    StateType.CRASHED: JobStatus.FAILURE,
    StateType.PAUSED: JobStatus.QUEUED,
}


class JobService:
    """Service for job management operations"""

    def __init__(self, db: AsyncSession, mongodb: AsyncIOMotorDatabase):
        self.db = db
        self.mongodb = mongodb
        self.chapter_service = ChapterService(db, mongodb)
        self.story_service = StoryService(db, mongodb)

    async def _get_prefect_client(self) -> PrefectClient:
        """Get Prefect client"""
        return get_client()

    @log_errors
    async def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Get detailed status of a job by flow run ID"""
        async with await self._get_prefect_client() as client:
            try:
                flow_run = await client.read_flow_run(UUID(job_id))
            except Exception:
                return JobStatusResponse(
                    job_id=job_id,
                    status=JobStatus.PENDING,
                    message="Job not found or expired",
                )

            # Map Prefect state to our status
            state_type = flow_run.state.type if flow_run.state else StateType.PENDING
            job_status = STATE_TYPE_MAP.get(state_type, JobStatus.PENDING)

            response = JobStatusResponse(
                job_id=job_id,
                status=job_status,
                queued_at=flow_run.created,
                started_at=flow_run.start_time,
                completed_at=flow_run.end_time,
            )

            # Handle different states
            if state_type == StateType.RUNNING:
                response.message = "Processing..."
                # Try to get progress from flow run state data
                if flow_run.state and flow_run.state.state_details:
                    details = flow_run.state.state_details
                    # Prefect stores task run counts in state details
                    # We can estimate progress from this

            elif state_type == StateType.COMPLETED:
                response.message = "Task complete!"
                # Try to get result
                if flow_run.state:
                    try:
                        result = await flow_run.state.result(raise_on_failure=False)
                        if isinstance(result, dict):
                            response.result = result
                            if result.get("chapters_extracted"):
                                count = result["chapters_extracted"]
                                response.message = f"Successfully extracted {count} chapter{'s' if count != 1 else ''}!"
                            elif result.get("edits_count"):
                                count = result["edits_count"]
                                response.message = f"Generated {count} line edit{'s' if count != 1 else ''}!"
                    except Exception:
                        pass

            elif state_type == StateType.FAILED:
                response.message = "Task failed"
                if flow_run.state and flow_run.state.message:
                    response.error = flow_run.state.message

            elif state_type in [StateType.SCHEDULED, StateType.PENDING]:
                response.message = "Task queued, waiting to start"

            return response
        
    @log_errors
    async def _cancel_all_jobs(
        self,
        chapter_id: str,
        job_type: Optional[str] = None
    ) -> dict:
        async with await self._get_prefect_client() as client:
            tag_filter = [f"chapter:{chapter_id}"]
            if job_type:
                tag_filter.append(job_type)

            flow_runs = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(
                    tags=FlowRunFilterTags(all_=tag_filter),
                    state=FlowRunFilterState(
                        type=FlowRunFilterStateType(any_=[StateType.RUNNING, StateType.PENDING, StateType.SCHEDULED])
                    )
                )
            )

            cancelled = 0
            for flow_run in flow_runs:
                try:
                    await client.set_flow_run_state(
                        flow_run_id=flow_run.id,
                        state=Cancelled(message=f"Flow cancelled by user for chapter {chapter_id}")
                    )
                    cancelled += 1
                    logger.info(f"Cancelled job {flow_run.id} for chapter {chapter_id}")
                except Exception as e:
                    logger.info(f"Failed to cancel flow run {flow_run.id}: {e}")

            return {
                "chapter_id": chapter_id,
                "jobs_cancelled": cancelled,
                "job_type": job_type
            }


    @log_errors
    async def queue_line_edit_job(
        self,
        chapter_id: str,
        user_id: str,
        force: bool = False,
    ) -> JobQueuedResponse:
        """Queue line edit generation for a chapter"""
        chapter = await self.chapter_service.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )
        
        # cancel all line edit jobs first
        cancel_result = await self._cancel_all_jobs(chapter_id, job_type="line-edit")

        if cancel_result.get("jobs_cancelled", 0) > 0:
            logger.info(
                f"Cancelled {cancel_result['jobs_cancelled']} "
                f"{cancel_result['job_type']} job(s) for chapter {chapter_id}"
            )

        # Check MongoDB for line edit status
        chapter_edits = await self.mongodb.chapter_edits.find_one({"chapter_id": chapter_id})
        is_stale = chapter_edits.get("is_stale", False) if chapter_edits else False
        last_generated_at = chapter_edits.get("last_generated_at") if chapter_edits else None
        
        # Check if line edits were recently generated
        # Skip the check if edits are stale (content changed) or force flag is set
        if not force and not is_stale and last_generated_at:
            time_since = datetime.utcnow() - last_generated_at
            if time_since < timedelta(hours=24):
                hours_ago = time_since.seconds // 3600
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Line edits generated {hours_ago}h ago. Use force=true to regenerate.",
                )
        
        # Log if we're regenerating due to stale edits
        if is_stale:
            logger.info(f"Regenerating line edits for chapter {chapter_id} (marked as stale due to content change)")

        story = await self.db.get(Story, chapter.story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!",
            )

        chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)

        # Submit flow to Prefect deployment (runs on worker container)
        flow_run = cast(FlowRun, await run_deployment(
            name="line-edits/line-edits-deployment",
            parameters={
                "chapter_id": chapter.id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "story_context": story.story_context or "",
                "chapter_content": chapter.content
            },
            timeout=0,
            tags=[f"chapter:{chapter_id}", "line-edits"]
        ))
        
        flow_run_id = str(flow_run.id)

        logger.info(
            f"Queued line edit job for Chapter {chapter_number} "
            f"'{chapter.title}' (flow_run_id: {flow_run_id})"
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Line Edits - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.LINE_EDIT,
            started_at=datetime.utcnow(),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=60,
        )

    async def _build_accumulated_context(
        self,
        story: Story,
        chapter_number: int,
    ) -> str:
        """Build accumulated context from all previous chapters' condensed contexts"""
        if not story.path_array or chapter_number <= 1:
            return ""
        
        # Get chapter IDs before current chapter
        previous_chapter_ids = story.path_array[:chapter_number - 1]
        if not previous_chapter_ids:
            return ""
        
        # Fetch previous chapters
        query = select(Chapter).where(Chapter.id.in_(previous_chapter_ids))  # type: ignore[union-attr]
        result = await self.db.execute(query)
        previous_chapters = {ch.id: ch for ch in result.scalars().all()}
        
        # Build accumulated context in order
        contexts = []
        for ch_id in previous_chapter_ids:
            ch = previous_chapters.get(ch_id)
            if ch and ch.condensed_context:
                contexts.append(f"=== Chapter {previous_chapter_ids.index(ch_id) + 1} ===\n{ch.condensed_context}")
        
        return "\n\n".join(contexts)
    
    @log_errors
    async def queue_reextraction_job(
        self,
        deleted_chapter_id: str,
        story_id: str,
        chapter_ids: List[str],
    ) -> JobQueuedResponse:
        """Queue a reextraction job after chapter deletion"""

        flow_run = cast(FlowRun, await run_deployment(
            name="reextraction-flow/chapter-reextraction-deployment",
            parameters={
                "story_id": story_id,
                "chapter_ids": chapter_ids,
            },
            timeout=0,
            tags=[*[f"chapter:{chapter_id}" for chapter_id in chapter_ids], "reextraction", "extraction"]
        ))
        flow_run_id = str(flow_run.id)

        logger.info(f"Queued reextraction for Chapters: {chapter_ids}")

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Reextraction after chapter: {deleted_chapter_id} deletion",
            job_type=JobType.REEXTRACTION,
            started_at=datetime.utcnow()
        )

    @log_errors
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
        force: bool = False,
    ) -> JobQueuedResponse:
        """Queue extraction for a single chapter"""
        chapter = await self.chapter_service.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found!",
            )
        
          # cancel all line edit jobs first
        cancel_result = await self._cancel_all_jobs(chapter_id, job_type="extraction")

        if cancel_result.get("jobs_cancelled", 0) > 0:
            logger.info(
                f"Cancelled {cancel_result['jobs_cancelled']} "
                f"{cancel_result['job_type']} job(s) for chapter {chapter_id}"
            )

        # Check if extraction needed (unless forced)
        if not force and not chapter.needs_extraction:
            word_delta = abs(chapter.word_count - (chapter.last_extracted_word_count or 0))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chapter doesn't need extraction (word delta: {word_delta} < 1000). Use force=true to override.",
            )

        story = await self.db.get(Story, chapter.story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!",
            )

        chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)
        estimated_duration = 60  # ~60s per chapter

        # Build accumulated context from previous chapters
        accumulated_context = await self._build_accumulated_context(story, chapter_number)

        # Submit flow to Prefect deployment (runs on worker container)
        flow_run = cast(FlowRun, await run_deployment(
            name="extract-single-chapter/chapter-extraction-deployment",
            parameters={
                "chapter_id": chapter.id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "word_count": chapter.word_count,
                "accumulated_context": accumulated_context,
                "content": chapter.content
            },
            timeout=0,
            tags=[f"chapter:{chapter_id}", "extraction"]
        ))
        
        flow_run_id = str(flow_run.id)

        logger.info(
            f"Queued extraction for Chapter {chapter_number} "
            f"'{chapter.title}' (flow_run_id: {flow_run_id})"
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Extraction - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.EXTRACTION,
            started_at=datetime.utcnow(),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=estimated_duration,
        )


async def get_job_service(
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> JobService:
    """Dependency for JobService"""
    return JobService(db=db, mongodb=mongodb)
