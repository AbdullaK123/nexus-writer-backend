"""
Line edits flow for generating prose improvements.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from prefect import flow, get_client, task
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
from src.infrastructure.config.prefect import DEFAULT_TASK_RETRIES, DEFAULT_TASK_RETRY_DELAY, EXTRACTION_TASK_TIMEOUT
from src.infrastructure.config import settings
from src.infrastructure.db.mongodb import MongoDB
from src.service.flows.publisher import FlowPublisher, create_flow_pubsub
from prefect import flow, get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterTags,
    FlowRunFilterState,
    FlowRunFilterStateType,
)
from prefect.client.schemas.objects import StateType
import asyncio

async def _wait_for_predecessor_extractions(
    story_id: str,
    chapter_number: int,
    story_path_array: List[str],
    pub: FlowPublisher,
    poll_interval: int = 5,
    max_wait: int = 600,
) -> None:
    """Poll until all predecessor chapter extractions finish.
    
    This runs INSIDE the flow (not in the API server), so all sibling
    flow runs are already registered in Prefect and visible.
    """
    if chapter_number <= 1:
        return

    predecessor_ids = set(story_path_array[:chapter_number - 1])
    if not predecessor_ids:
        return

    elapsed = 0
    while elapsed < max_wait:
        async with get_client() as client:
            flow_runs = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(
                    tags=FlowRunFilterTags(all_=["extraction", f"story:{story_id}"]),
                    state=FlowRunFilterState(
                        type=FlowRunFilterStateType(any_=[
                            StateType.RUNNING,
                            StateType.PENDING,
                            StateType.SCHEDULED,
                        ])
                    )
                )
            )

        blocking: List[str] = []
        for fr in flow_runs:
            for tag in fr.tags:
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

        await pub.task_started("predecessor_wait", message=f"Waiting on {len(blocking)} predecessor(s)")
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



@task(
    name="generate-line-edits",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAY,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def generate_line_edits_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    use_lfm: bool = False,
    story_id: str = "",
) -> ChapterEdit:
    """Generate line edits for chapter"""
    log.debug("task.line_edits.start", chapter_number=chapter_number, story_id=story_id)
    return await generate_line_edits(
        story_context, 
        chapter_content, 
        chapter_number, 
        chapter_title,
        use_lfm=use_lfm,
        story_id=story_id,
    )


@task(
    name="save-line-edits",
    retries=2,
    retry_delay_seconds=[5, 10],
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


@flow(
    name="line-edits",
    retries=1,
    retry_delay_seconds=15,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
    persist_result=True,
)
async def line_edits_flow(
    story_id: str,
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    story_context: str,
    story_path_array: List[str],
    chapter_content: str,
    user_id: str = "",
    use_lfm: bool = False,
) -> Dict[str, Any]:
    """Generate line edits for a chapter."""
    pubsub = create_flow_pubsub(settings.redis_url, LineEditsEventData) #type: ignore
    pub = FlowPublisher[LineEditsEventData](
        pubsub=pubsub,
        user_id=user_id,
        story_id=story_id,
        job_type=JobType.LINE_EDIT,
        total_steps=3,
    )
    await pub.flow_started(data=ChapterStartedData(chapter_id=chapter_id, chapter_number=chapter_number))

    # Step 1: Wait for predecessor extractions
    await _wait_for_predecessor_extractions(
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
            use_lfm=use_lfm,
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