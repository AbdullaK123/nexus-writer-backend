"""
Line edits flow for generating prose improvements.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from prefect import flow, get_client, task
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger
from app.ai.edits import generate_line_edits
from app.ai.models.edits import ChapterEdit, ChapterEdits
from app.core.database import engine
from app.models import Chapter
from app.config.prefect import DEFAULT_TASK_RETRIES, DEFAULT_TASK_RETRY_DELAY, EXTRACTION_TASK_TIMEOUT
from app.core.mongodb import MongoDB
from app.config.settings import app_config
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
                logger.info(f"Chapter {chapter_number}: predecessors complete after {elapsed}s wait")
            return

        logger.info(
            f"Chapter {chapter_number}: waiting for {len(blocking)} predecessor(s) "
            f"({elapsed}s / {max_wait}s)"
        )
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    logger.warning(
        f"Chapter {chapter_number}: predecessors still running after {max_wait}s, proceeding anyway"
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
) -> ChapterEdit:
    """Generate line edits for chapter"""
    return await generate_line_edits(
        story_context, 
        chapter_content, 
        chapter_number, 
        chapter_title
    )


@task(
    name="save-line-edits",
    retries=2,
    retry_delay_seconds=[5, 10],
)
async def save_line_edits_task(
    chapter_id: str,
    chapter_number: int,
    line_edits: ChapterEdit,
) -> None:
    """Save line edits to MongoDB only"""
    async with AsyncSession(engine) as db:


        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")
        
        mongo_db = MongoDB.db
        if mongo_db is None:
            raise ValueError("MongoDB not connected")
        
        # Save to MongoDB
        await mongo_db.chapter_edits.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "user_id": chapter.user_id,
                "chapter_number": chapter_number,
                "edits": [edit.model_dump() for edit in line_edits.edits],
                "last_generated_at": datetime.utcnow(),
                "is_stale": False
            },
            upsert=True
        )
        logger.info(f"✅ Saved {len(line_edits.edits)} edits to MongoDB")
        
    logger.info(f"✅ Line edits saved for chapter {chapter_id}")


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
    chapter_content: str
) -> Dict[str, Any]:
    """Generate line edits for a chapter."""
    await MongoDB.connect(app_config.mongodb_url)

    await _wait_for_predecessor_extractions(
        story_id, 
        chapter_number,
        story_path_array
     )
    
    logger.info(f"Starting line edits for Chapter {chapter_number}")
    
    # Generate line edits
    edits = await generate_line_edits_task(
        story_context=story_context,
        chapter_content=chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
    )
    
    # Save to database
    await save_line_edits_task(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        line_edits=edits,
    )
    
    logger.success(
        f"✅ Line edits complete for Chapter {chapter_number}: "
        f"{len(edits.edits)} edits generated"
    )
    
    return {
        "chapter_id": chapter_id,
        "chapter_number": chapter_number,
        "success": True,
        "edits_count": len(edits.edits),
    }