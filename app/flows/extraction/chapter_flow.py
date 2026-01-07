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
    """
    logger.info(f"Starting extraction for Chapter {chapter_number} ({chapter_id})")
    
    try:
        # Run all 4 extractions concurrently (batched for performance)
        character_result = await extract_characters_task(
            accumulated_context, content, chapter_number, chapter_title
        )
        plot_result = await extract_plot_task(
            accumulated_context, content, chapter_number, chapter_title
        )
        world_result = await extract_world_task(
            accumulated_context, content, chapter_number, chapter_title
        )
        structure_result = await extract_structure_task(
            accumulated_context, content, chapter_number, chapter_title
        )
        
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
        
    except Exception as e:
        # Unexpected error - will be retried by Prefect
        logger.error(f"Chapter {chapter_number} extraction failed: {e}")
        raise  # Let Prefect handle retry
