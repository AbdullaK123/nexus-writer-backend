"""
Job provider for managing background tasks via Prefect.

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
from prefect.client.orchestration import PrefectClient
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
)
from app.providers.chapter import ChapterProvider
from app.providers.story import StoryProvider
from app.utils.decorators import log_errors


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


class JobProvider:
    """Provider for job management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chapter_provider = ChapterProvider(db)
        self.story_provider = StoryProvider(db)

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
    async def queue_line_edit_job(
        self,
        chapter_id: str,
        user_id: str,
        force: bool = False,
    ) -> JobQueuedResponse:
        """Queue line edit generation for a chapter"""
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        # Check if line edits were recently generated
        if not force and chapter.line_edits_generated_at:
            time_since = datetime.utcnow() - chapter.line_edits_generated_at
            if time_since < timedelta(hours=24):
                hours_ago = time_since.seconds // 3600
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Line edits generated {hours_ago}h ago. Use force=true to regenerate.",
                )

        story = await self.db.get(Story, chapter.story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found!",
            )

        chapter_number = chapter.chapter_number

        # Submit flow to Prefect deployment (runs on worker container)
        flow_run = cast(FlowRun, await run_deployment(
            name="line-edits/line-edits-deployment",
            parameters={
                "chapter_id": chapter.id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "story_context": story.story_context or "",
                "chapter_content": chapter.content,
                "user_id": user_id,
                "story_id": story.id,
            },
            timeout=0,  # Don't wait for completion
        ))
        
        flow_run_id = str(flow_run.id)

        logger.info(
            f"Queued line edit job for Chapter {chapter_number} "
            f"'{chapter.title}' (flow_run_id: {flow_run_id})"
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Line Edits - Chapter {chapter_number}: {chapter.title}",
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
    async def queue_extraction_job(
        self,
        user_id: str,
        chapter_id: str,
        force: bool = False,
    ) -> JobQueuedResponse:
        """Queue extraction for a single chapter"""
        chapter = await self.chapter_provider.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found!",
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

        chapter_number = chapter.chapter_number
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
                "content": chapter.content,
                "story_id": story.id,
                "user_id": user_id,
            },
            timeout=0,  # Don't wait for completion
        ))
        
        flow_run_id = str(flow_run.id)

        logger.info(
            f"Queued extraction for Chapter {chapter_number} "
            f"'{chapter.title}' (flow_run_id: {flow_run_id})"
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Extraction - Chapter {chapter_number}: {chapter.title}",
            started_at=datetime.utcnow(),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=estimated_duration,
        )


async def get_job_provider(
    db: AsyncSession = Depends(get_db),
) -> JobProvider:
    """Dependency for JobProvider"""
    return JobProvider(db=db)
