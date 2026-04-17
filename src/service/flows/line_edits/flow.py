"""
Line edits job for generating prose improvements.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.service.ai.edits import generate_line_edits
from src.data.models.ai.edits import ChapterEdit, ChapterEdits
from src.data.schemas.jobs import (
    JobType,
    LineEditsEventData,
    ChapterStartedData,
    EditsGeneratedData,
    LineEditsCompleteData,
)
from src.infrastructure.config import settings, config
from src.infrastructure.db.mongodb import MongoDB
from src.infrastructure.redis.job_registry import JobRegistry, RegistryStatus
from src.service.flows.publisher import FlowPublisher
import asyncio

async def _wait_for_predecessor_extractions(
    registry: JobRegistry,
    story_id: str,
    chapter_number: int,
    story_path_array: List[str],
    pub: FlowPublisher,
    poll_interval: int = config.worker.predecessor_poll_interval,
    max_wait: int = config.worker.predecessor_max_wait,
) -> None:
    """Poll until all predecessor chapter extractions finish.

    Uses JobRegistry tag-based filtering instead of Prefect API.
    """
    if chapter_number <= 1:
        return

    predecessor_ids = set(story_path_array[:chapter_number - 1])
    if not predecessor_ids:
        return

    await pub.task_started("predecessor_wait", message="Waiting for predecessor extractions")
    elapsed = 0
    while elapsed < max_wait:
        active_jobs = await registry.find_by_tags(
            ["extraction", f"story:{story_id}"],
            statuses=[RegistryStatus.QUEUED, RegistryStatus.RUNNING],
        )

        blocking: List[str] = []
        for job_id in active_jobs:
            tags = await registry.get_tags(job_id)
            for tag in tags:
                if tag.startswith("chapter:"):
                    ch_id = tag.split(":", 1)[1]
                    if ch_id in predecessor_ids:
                        blocking.append(ch_id)

        if not blocking:
            if elapsed > 0:
                log.info("line_edits.predecessors_complete", chapter_number=chapter_number, waited_seconds=elapsed)
                await pub.task_complete("predecessor_wait", message=f"Predecessors ready after {elapsed}s")
            else:
                await pub.task_complete("predecessor_wait", message="No predecessors blocking")
            return

        log.info(
            "line_edits.waiting_for_predecessors",
            chapter_number=chapter_number,
            blocking_count=len(blocking),
            elapsed_seconds=elapsed,
            max_wait_seconds=max_wait,
        )
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    await pub.task_failed("predecessor_wait", message=f"Timed out after {max_wait}s")
    log.warning(
        "line_edits.predecessors_timeout",
        chapter_number=chapter_number,
        max_wait_seconds=max_wait,
    )



async def generate_line_edits_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> ChapterEdit:
    """Generate line edits for chapter"""
    log.debug("task.line_edits.start", chapter_number=chapter_number, story_id=story_id)
    return await generate_line_edits(
        story_context, 
        chapter_content, 
        chapter_number, 
        chapter_title,
        story_id=story_id,
    )


async def save_line_edits_task(
    chapter_id: str,
    story_id: str,
    user_id: str,
    chapter_number: int,
    line_edits: ChapterEdit,
) -> None:
    """Save line edits to MongoDB."""
    mongo_db = MongoDB.db
    if mongo_db is None:
        raise ValueError("MongoDB not connected")

    await mongo_db.chapter_edits.replace_one(
        {"chapter_id": chapter_id},
        {
            "chapter_id": chapter_id,
            "story_id": story_id,
            "user_id": user_id,
            "chapter_number": chapter_number,
            "edits": [edit.model_dump() for edit in line_edits.edits],
            "last_generated_at": datetime.now(timezone.utc),
            "is_stale": False
        },
        upsert=True
    )
    log.info("task.line_edits_saved", chapter_id=chapter_id, edit_count=len(line_edits.edits))


async def _run_line_edits(
    registry: JobRegistry,
    job_run_id: str,
    *,
    story_id: str,
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    story_context: str,
    story_path_array: List[str],
    chapter_content: str,
    user_id: str = "",
) -> Dict[str, Any]:
    """Core line edits logic."""
    pub = FlowPublisher[LineEditsEventData](
        redis_url=settings.redis_url,
        user_id=user_id,
        story_id=story_id,
        job_type=JobType.LINE_EDIT,
        total_steps=3,
        job_run_id=job_run_id,
    )
    try:
        await pub.flow_started(data=ChapterStartedData(chapter_id=chapter_id, chapter_number=chapter_number))

        # Step 1: Wait for predecessor extractions
        await _wait_for_predecessor_extractions(
            registry,
            story_id, 
            chapter_number,
            story_path_array,
            pub=pub,
        )
    
        log.info("line_edits.started", chapter_number=chapter_number, chapter_id=chapter_id)
    
        # Step 2: Generate line edits
        await pub.task_started("generate_line_edits", message="Generating line edits")
        try:
            edits = await generate_line_edits_task(
                story_context=story_context,
                chapter_content=chapter_content,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                story_id=story_id,
            )
            await pub.task_complete("generate_line_edits", data=EditsGeneratedData(edits_count=len(edits.edits)))
        except Exception as e:
            await pub.task_failed("generate_line_edits", message=str(e))
            await pub.flow_failed(message=str(e))
            raise
    
        # Step 3: Save to database
        await pub.task_started("save_line_edits", message="Saving edits")
        try:
            await save_line_edits_task(
                chapter_id=chapter_id,
                story_id=story_id,
                user_id=user_id,
                chapter_number=chapter_number,
                line_edits=edits,
            )
            await pub.task_complete("save_line_edits")
        except Exception as e:
            await pub.task_failed("save_line_edits", message=str(e))
            await pub.flow_failed(message=str(e))
            raise
    
        log.success(
            "line_edits.complete",
            chapter_number=chapter_number,
            chapter_id=chapter_id,
            edit_count=len(edits.edits),
        )

        result = {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "success": True,
            "edits_count": len(edits.edits),
        }
        await pub.flow_complete(data=LineEditsCompleteData(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            edits_count=len(edits.edits),
        ))
    
        return result
    finally:
        await pub.close()


async def line_edits_job(ctx: dict, **kwargs) -> Dict[str, Any]:
    """arq job entry point — wraps _run_line_edits with registry status tracking."""
    registry: JobRegistry = ctx["registry"]
    job_id: str = ctx["job_id"]
    await registry.set_status(job_id, RegistryStatus.RUNNING)
    try:
        result = await _run_line_edits(registry, job_id, **kwargs)
        await registry.set_status(job_id, RegistryStatus.COMPLETE)
        return result
    except Exception:
        await registry.set_status(job_id, RegistryStatus.FAILED)
        raise