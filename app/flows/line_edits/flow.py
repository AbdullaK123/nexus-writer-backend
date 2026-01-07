"""
Line edits flow for generating prose improvements.

Simple single-task flow with retry policies.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from prefect import flow, task
from prefect.runtime import flow_run
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.ai.edits import generate_line_edits
from app.ai.models.edits import ChapterEdit
from app.core.database import engine
from app.models import Chapter
from app.config.prefect import DEFAULT_TASK_RETRIES, DEFAULT_TASK_RETRY_DELAYS, EXTRACTION_TASK_TIMEOUT


@task(
    name="generate-line-edits",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def generate_line_edits_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
) -> list[dict]:
    """Generate line edits for chapter"""
    try:
        result: ChapterEdit = await generate_line_edits(
            story_context, chapter_content, chapter_number, chapter_title
        )
        return [edit.model_dump() for edit in result.edits]
    except Exception as e:
        raise


@task(
    name="save-line-edits",
    retries=2,
    retry_delay_seconds=[5, 10],
)
async def save_line_edits_task(
    chapter_id: str,
    line_edits: list[dict],
) -> None:
    """Save line edits to database"""
    try:
        async with AsyncSession(engine) as db:
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            chapter.line_edits = line_edits
            chapter.line_edits_generated_at = datetime.utcnow()
            
            await db.commit()
            
        logger.info(f"✅ Line edits saved for chapter {chapter_id}")
        
    except Exception as e:
        raise


@flow(
    name="line-edits",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=600,  # 10 minutes
    persist_result=True,
)
async def line_edits_flow(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    story_context: str,
    chapter_content: str,
    user_id: str,
    story_id: str,
) -> Dict[str, Any]:
    """
    Generate line edits for a chapter.
    
    Returns dict with status and edit count.
    """
    logger.info(f"Starting line edits for Chapter {chapter_number}")
    
    try:
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
            line_edits=edits,
        )
        
        logger.success(
            f"✅ Line edits complete for Chapter {chapter_number}: "
            f"{len(edits)} edits generated"
        )
        
        return {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "success": True,
            "edits_count": len(edits),
        }
        
    except Exception as e:
        logger.error(f"Line edits failed: {e}")
        raise
