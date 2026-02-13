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
from app.config.settings import app_config
from app.core.mongodb import MongoDB
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
    content: str
) -> ChapterExtractionResult:
    """Extract context from a single chapter with checkpointing."""
    
    await MongoDB.connect(app_config.mongodb_url)

    logger.info(f"Starting extraction for Chapter {chapter_number} ({chapter_id})")

    # Run all 4 extractions concurrently
    async with asyncio.TaskGroup() as tg:
        character_task = tg.create_task(
            extract_characters_task(accumulated_context, content, chapter_number, chapter_title)
        )
        plot_task = tg.create_task(
            extract_plot_task(accumulated_context, content, chapter_number, chapter_title)
        )
        world_task = tg.create_task(
            extract_world_task(accumulated_context, content, chapter_number, chapter_title)
        )
        structure_task = tg.create_task(
            extract_structure_task(accumulated_context, content, chapter_number, chapter_title)
        )
    
    # Get results (typed models, not dicts)
    character_result = character_task.result()
    plot_result = plot_task.result()
    world_result = world_task.result()
    structure_result = structure_task.result()
    
    logger.info(f"Chapter {chapter_number}: All extractions complete, synthesizing...")
    
    # Synthesize into condensed context
    synthesis_result = await synthesize_context_task(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        word_count=word_count,
        character_extraction=character_result.model_dump(),  # ✅ Convert to dict
        plot_extraction=plot_result.model_dump(),
        world_extraction=world_result.model_dump(),
        structure_extraction=structure_result.model_dump(),
    )
    
    # CHECKPOINT: Save to database immediately
    await save_chapter_extraction_task(
        chapter_id=chapter_id,
        chapter_number=chapter_number,  # ✅ Add missing parameter
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
        condensed_context=synthesis_result.condensed_text,  
        character_extraction=character_result.model_dump(), 
        plot_extraction=plot_result.model_dump(),
        world_extraction=world_result.model_dump(),
        structure_extraction=structure_result.model_dump(),
    )