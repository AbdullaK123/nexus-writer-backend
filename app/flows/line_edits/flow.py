"""
Line edits flow for generating prose improvements.

Simple single-task flow with circuit breaker protection.
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
from app.flows.circuit_breaker import gemini_breaker, database_breaker, CircuitOpenError
from app.flows.dlq import dlq_service
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
    if not gemini_breaker.can_execute():
        ttr = gemini_breaker.time_to_recovery()
        raise CircuitOpenError("gemini-api", ttr or 0)
    
    try:
        result: ChapterEdit = await generate_line_edits(
            story_context, chapter_content, chapter_number, chapter_title
        )
        gemini_breaker.record_success()
        return [edit.model_dump() for edit in result.edits]
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
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
    if not database_breaker.can_execute():
        ttr = database_breaker.time_to_recovery()
        raise CircuitOpenError("postgres", ttr or 0)
    
    try:
        async with AsyncSession(engine) as db:
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            chapter.line_edits = line_edits
            chapter.line_edits_generated_at = datetime.utcnow()
            
            await db.commit()
            
        database_breaker.record_success()
        logger.info(f"✅ Line edits saved for chapter {chapter_id}")
        
    except CircuitOpenError:
        raise
    except Exception as e:
        database_breaker.record_failure()
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
        
    except CircuitOpenError as e:
        logger.warning(f"Line edits aborted: circuit breaker open")
        
        # Send to DLQ
        flow_run_id = str(flow_run.get_id()) if flow_run.get_id() else "unknown"
        await dlq_service.send_to_dlq(
            flow_run_id=flow_run_id,
            flow_name="line-edits",
            user_id=user_id,
            input_payload={
                "chapter_id": chapter_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
            },
            error=e,
            retry_count=2,
            chapter_id=chapter_id,
            story_id=story_id,
        )
        
        return {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "success": False,
            "error": str(e),
        }
        
    except Exception as e:
        logger.error(f"Line edits failed: {e}")
        
        # Send to DLQ on final failure
        flow_run_id = str(flow_run.get_id()) if flow_run.get_id() else "unknown"
        await dlq_service.send_to_dlq(
            flow_run_id=flow_run_id,
            flow_name="line-edits",
            user_id=user_id,
            input_payload={
                "chapter_id": chapter_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
            },
            error=e,
            retry_count=2,
            chapter_id=chapter_id,
            story_id=story_id,
        )
        
        raise
