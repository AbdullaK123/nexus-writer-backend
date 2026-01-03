"""
Tier 2: Single chapter extraction sub-flow with checkpointing.

This flow:
- Runs all 4 AI extractions concurrently (batched)
- Synthesizes results
- Commits to database immediately (checkpoint)
- Returns results for rolling context
"""
import asyncio
from dataclasses import dataclass
from typing import Optional
from prefect import flow
from prefect.runtime import flow_run
from loguru import logger

from app.flows.extraction.tasks import (
    extract_characters_task,
    extract_plot_task,
    extract_world_task,
    extract_structure_task,
    synthesize_context_task,
    save_chapter_extraction_task,
)
from app.flows.circuit_breaker import CircuitOpenError
from app.flows.dlq import dlq_service
from app.config.prefect import DEFAULT_FLOW_RETRIES, CHAPTER_FLOW_TIMEOUT


@dataclass
class ChapterExtractionResult:
    """Result from single chapter extraction"""
    chapter_id: str
    chapter_number: int
    success: bool
    condensed_context: Optional[str] = None
    character_extraction: Optional[dict] = None
    plot_extraction: Optional[dict] = None
    world_extraction: Optional[dict] = None
    structure_extraction: Optional[dict] = None
    error: Optional[str] = None


async def _handle_chapter_failure(
    chapter_id: str,
    chapter_number: int,
    story_id: str,
    user_id: str,
    accumulated_context: str,
    content: str,
    error: Exception,
) -> None:
    """Send failed chapter extraction to DLQ"""
    try:
        flow_run_id = str(flow_run.get_id()) if flow_run.get_id() else "unknown"
        
        await dlq_service.send_to_dlq(
            flow_run_id=flow_run_id,
            flow_name="extract-single-chapter",
            user_id=user_id,
            input_payload={
                "chapter_id": chapter_id,
                "chapter_number": chapter_number,
                "story_id": story_id,
                "accumulated_context_length": len(accumulated_context),
                "content_length": len(content),
            },
            error=error,
            retry_count=DEFAULT_FLOW_RETRIES,
            chapter_id=chapter_id,
            story_id=story_id,
        )
    except Exception as dlq_error:
        logger.error(f"Failed to send to DLQ: {dlq_error}")


@flow(
    name="extract-single-chapter",
    retries=DEFAULT_FLOW_RETRIES,
    retry_delay_seconds=60,
    timeout_seconds=CHAPTER_FLOW_TIMEOUT,
    persist_result=True,
)
async def extract_single_chapter_flow(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    accumulated_context: str,
    content: str,
    story_id: str,
    user_id: str,
) -> ChapterExtractionResult:
    """
    Extract context from a single chapter with checkpointing.
    
    This flow:
    1. Runs 4 AI extractions concurrently
    2. Synthesizes into condensed context
    3. Saves to database immediately (checkpoint)
    
    On failure after retries, sends to DLQ for manual review.
    """
    logger.info(f"Starting extraction for Chapter {chapter_number} ({chapter_id})")
    
    try:
        # Check circuit breaker before starting expensive work
        from app.flows.circuit_breaker import gemini_breaker
        if not gemini_breaker.can_execute():
            ttr = gemini_breaker.time_to_recovery()
            raise CircuitOpenError("gemini-api", ttr or 0)
        
        # Run all 4 extractions concurrently (batched for performance)
        character_future = extract_characters_task.submit(
            accumulated_context, content, chapter_number, chapter_title
        )
        plot_future = extract_plot_task.submit(
            accumulated_context, content, chapter_number, chapter_title
        )
        world_future = extract_world_task.submit(
            accumulated_context, content, chapter_number, chapter_title
        )
        structure_future = extract_structure_task.submit(
            accumulated_context, content, chapter_number, chapter_title
        )
        
        # Wait for all extractions
        character_result = character_future.result()
        plot_result = plot_future.result()
        world_result = world_future.result()
        structure_result = structure_future.result()
        
        logger.info(f"Chapter {chapter_number}: All extractions complete, synthesizing...")
        
        # Synthesize into condensed context
        synthesis_result = await synthesize_context_task(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            word_count=word_count,
            character_extraction=character_result,
            plot_extraction=plot_result,
            world_extraction=world_result,
            structure_extraction=structure_result,
        )
        
        # CHECKPOINT: Save to database immediately
        await save_chapter_extraction_task(
            chapter_id=chapter_id,
            character_extraction=character_result,
            plot_extraction=plot_result,
            world_extraction=world_result,
            structure_extraction=structure_result,
            context_synthesis=synthesis_result,
            word_count=word_count,
        )
        
        logger.success(f"✅ Chapter {chapter_number} extraction complete and checkpointed")
        
        return ChapterExtractionResult(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            success=True,
            condensed_context=synthesis_result.get("condensed_text"),
            character_extraction=character_result,
            plot_extraction=plot_result,
            world_extraction=world_result,
            structure_extraction=structure_result,
        )
        
    except CircuitOpenError as e:
        # Circuit breaker open - don't retry, abort flow
        logger.warning(f"Chapter {chapter_number}: Circuit breaker open, aborting")
        
        await _handle_chapter_failure(
            chapter_id, chapter_number, story_id, user_id,
            accumulated_context, content, e
        )
        
        return ChapterExtractionResult(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            success=False,
            error=f"Circuit breaker open: {e}",
        )
        
    except Exception as e:
        # Unexpected error - will be retried by Prefect
        logger.error(f"Chapter {chapter_number} extraction failed: {e}")
        
        # If this is the final retry, send to DLQ
        # (Prefect will call this after all retries exhausted)
        await _handle_chapter_failure(
            chapter_id, chapter_number, story_id, user_id,
            accumulated_context, content, e
        )
        
        raise  # Let Prefect handle retry
