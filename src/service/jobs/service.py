"""
Job service for managing background tasks via Prefect.

Handles:
- Queuing new extraction and line edit jobs
- Polling job status
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, cast
from uuid import UUID

from src.service.exceptions import NotFoundError, ValidationError
from prefect import get_client
from prefect.client.schemas.objects import StateType, FlowRun
from prefect.client.schemas.filters import FlowRunFilter, FlowRunFilterTags, FlowRunFilterState, FlowRunFilterStateType
from prefect.client.orchestration import PrefectClient
from prefect.states import Cancelled
from prefect.deployments import run_deployment
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

    def __init__(self, mongodb: AsyncDatabase):
        self.mongodb = mongodb

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
                log.opt(exception=True).warning("job.status_lookup_failed", job_id=job_id)
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

            elif state_type == StateType.COMPLETED:
                response.message = "Task complete!"
                # Try to get result
                if flow_run.state:
                    try:
                        result = await flow_run.state.result(raise_on_failure=False)  # type: ignore[misc]
                        if isinstance(result, dict):
                            response.result = result
                            if result.get("chapters_extracted"):
                                count = result["chapters_extracted"]
                                response.message = f"Successfully extracted {count} chapter{'s' if count != 1 else ''}!"
                            elif result.get("edits_count"):
                                count = result["edits_count"]
                                response.message = f"Generated {count} line edit{'s' if count != 1 else ''}!"
                    except Exception:
                        log.opt(exception=True).warning("job.result_retrieval_failed", job_id=job_id)

            elif state_type == StateType.FAILED:
                response.message = "Task failed"
                if flow_run.state and flow_run.state.message:
                    response.error = flow_run.state.message

            elif state_type in [StateType.SCHEDULED, StateType.PENDING]:
                response.message = "Task queued, waiting to start"

            return response
        
    @log_errors
    async def cancel_all_jobs(
        self,
        chapter_id: Optional[str] = None,
        story_id: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> dict:
        async with await self._get_prefect_client() as client:

            if chapter_id is None and story_id is None:
                log.info("job.cancel_skipped: no filters provided")
                return {
                    "jobs_cancelled": 0
                }

            if story_id:
                tag_filter = [f"story:{story_id}"]
            else: 
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
                        state=Cancelled(message=f"Flow cancelled by user for chapter {chapter_id} and story {story_id}")
                    )
                    cancelled += 1
                    log.info("job.cancelled", flow_run_id=str(flow_run.id), chapter_id=chapter_id, story_id=story_id)
                except Exception as e:
                    log.warning("job.cancel_failed", flow_run_id=str(flow_run.id), error=str(e))

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
            if time_since < timedelta(hours=24):
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

        # Submit flow to Prefect deployment (runs on worker container)
        flow_run = cast(FlowRun, await run_deployment(
            name="line-edits/line-edits-deployment",
            parameters={
                "story_id": story.id,
                "chapter_id": chapter.id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "story_context": accumulated_context or "",
                "story_path_array": story.path_array,
                "chapter_content": chapter.content,
                "user_id": user_id,
                "use_lfm": settings.use_lfm,
            },
            timeout=0,
            tags=[f"chapter:{chapter_id}", f"story:{story.id}", "line-edits"]
        ))
        
        flow_run_id = str(flow_run.id)

        log.info(
            "job.line_edit_queued",
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            chapter_id=chapter_id,
            flow_run_id=flow_run_id,
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Line Edits - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.LINE_EDIT,
            started_at=datetime.now(timezone.utc),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=60,
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

        flow_run = cast(FlowRun, await run_deployment(
            name="reextraction-flow/chapter-reextraction-deployment",
            parameters={
                "story_id": story_id,
                "chapter_ids": chapter_ids,
                "user_id": user_id,
                "use_lfm": settings.use_lfm,
            },
            timeout=0,
            tags=[*[f"chapter:{chapter_id}" for chapter_id in chapter_ids], f"story:{story_id}", "reextraction"]
        ))
        flow_run_id = str(flow_run.id)

        log.info("job.reextraction_queued", chapter_ids=chapter_ids, story_id=story_id, flow_run_id=flow_run_id)

        return JobQueuedResponse(
            job_id=flow_run_id,
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

        # Submit flow to Prefect deployment (runs on worker container)
        # Predecessor waiting and context building happen inside the flow
        flow_run = cast(FlowRun, await run_deployment(
            name="extract-single-chapter/chapter-extraction-deployment",
            parameters={
                "chapter_id": chapter.id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "word_count": chapter.word_count,
                "story_id": story.id,
                "story_path_array": story.path_array,
                "content": html_to_plain_text(chapter.content),
                "user_id": user_id,
                "use_lfm": settings.use_lfm,
            },
            timeout=0,
            tags=[f"chapter:{chapter_id}", f"story:{story.id}", "extraction"]
        ))
        
        flow_run_id = str(flow_run.id)

        log.info(
            "job.extraction_queued",
            chapter_number=chapter_number,
            chapter_title=chapter.title,
            chapter_id=chapter_id,
            flow_run_id=flow_run_id,
        )

        return JobQueuedResponse(
            job_id=flow_run_id,
            job_name=f"Extraction - Chapter {chapter_number}: {chapter.title}",
            job_type=JobType.EXTRACTION,
            started_at=datetime.now(timezone.utc),
            status=JobStatus.QUEUED,
            chapter_id=chapter.id,
            chapter_number=chapter_number,
            estimated_duration_seconds=60,
        )


