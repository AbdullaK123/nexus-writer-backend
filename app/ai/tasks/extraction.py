# app/ai/tasks/extraction.py

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.ai.character import extract_characters
from app.ai.plot import extract_plot_information
from app.ai.structure import extract_story_structure
from app.ai.world import extract_world_information
from app.ai.context import synthesize_chapter_context
from app.ai.models.context import CondensedChapterContext
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.world import WorldExtraction
import asyncio
from app.config.celery import celery_app
from app.core.database import get_db
from typing import Any, Dict, Optional, TypedDict
from loguru import logger
from datetime import datetime


class ExtractionResults(TypedDict):
    character: CharacterExtraction
    world: WorldExtraction
    plot: PlotExtraction
    structure: StructureExtraction
    context: CondensedChapterContext


async def get_condensed_context(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    story_context: str,
    current_chapter_content: str,
) -> ExtractionResults:
    """Run concurrent extractions for a chapter"""
    logger.info(f"Starting extraction for Chapter {chapter_number} (ID: {chapter_id})")
    
    # Run all 4 extractions in parallel using TaskGroup (Python 3.11+)
    async with asyncio.TaskGroup() as tg:
        character_task = tg.create_task(extract_characters(
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        ))
        plot_task = tg.create_task(extract_plot_information(
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        ))
        structure_task = tg.create_task(extract_story_structure(
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        ))
        world_task = tg.create_task(extract_world_information(
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        ))
    
    # TaskGroup ensures all tasks complete before continuing
    character_result = character_task.result()
    plot_result = plot_task.result()
    structure_result = structure_task.result()
    world_result = world_task.result()
    
    logger.info(f"Chapter {chapter_number}: All extractions complete, synthesizing...")
    
    # Synthesize the final condensed context
    final_result = await synthesize_chapter_context(
        chapter_id,
        chapter_number,
        chapter_title,
        word_count,
        character_result,
        plot_result,
        world_result,
        structure_result
    )
    
    logger.success(f"Chapter {chapter_number}: Synthesis complete!")
    
    return {
        "character": character_result,
        "plot": plot_result,
        "world": world_result,
        "structure": structure_result,
        "context": final_result
    }


async def save_extraction_results_to_db(
    db: AsyncSession,
    chapter_id: str,
    chapter_number: int,
    word_count: int,
    extraction_results: ExtractionResults
) -> Dict[str, Any]:
    """Save extraction results to database"""
    from app.models import Chapter

    try:
        # Use get() for async SQLModel
        chapter: Chapter | None = await db.get(Chapter, chapter_id)
        
        if not chapter:
            raise ValueError(f"Chapter with ID {chapter_id} does not exist!")
        
        # Update chapter with extraction results
        chapter.condensed_context = extraction_results["context"].condensed_text
        chapter.timeline_context = extraction_results["context"].timeline_context
        chapter.themes = extraction_results["context"].themes_present
        chapter.emotional_arc = extraction_results["context"].emotional_arc
        chapter.last_extracted_at = datetime.now()
        chapter.last_extracted_word_count = word_count
        
        # Store detailed extractions
        chapter.character_extraction = extraction_results["character"].model_dump()
        chapter.plot_extraction = extraction_results["plot"].model_dump()
        chapter.world_extraction = extraction_results["world"].model_dump()
        chapter.structure_extraction = extraction_results["structure"].model_dump()
        
        # Set extraction version for tracking
        chapter.extraction_version = "1.0.0"  # Bump when you improve prompts
        
        await db.commit()
        
        logger.info(f"Chapter {chapter_number} extraction results saved to database.")
        
        return {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "status": "success",
            "condensed_word_count": len(extraction_results["context"].condensed_text.split())
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save extraction results for Chapter {chapter_number}: {e}")
        raise


async def orchestrate_extraction(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    story_context: str,
    current_chapter_content: str,
    word_count: int
) -> Dict[str, Any]:
    """
    Orchestrate the full extraction pipeline with database operations.
    Creates its own database session.
    """
    # Create fresh async session for this task
    async with get_db() as db:
        # Run extractions
        extraction_results = await get_condensed_context(
            chapter_id,
            chapter_number,
            chapter_title,
            word_count,
            story_context,
            current_chapter_content
        )
        
        # Save to database
        db_result = await save_extraction_results_to_db(
            db,
            chapter_id,
            chapter_number,
            word_count,
            extraction_results
        )
        
        return db_result


@celery_app.task(bind=True, max_retries=3)
def extract_chapter_context(
    self,
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    story_context: str,
    current_chapter_content: str,
    word_count: int
):
    """
    Celery task for multi-pass chapter extraction with parallel processing.
    
    Runs 4 extraction passes concurrently, then synthesizes results.
    
    Args:
        chapter_id: UUID of the chapter
        chapter_number: Chapter sequence number
        chapter_title: Optional chapter title
        story_context: Accumulated condensed context from previous chapters
        current_chapter_content: Raw chapter text
        word_count: Current word count
    """
    try:
        logger.info(f"Celery worker: Starting extraction for Chapter {chapter_number}")
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async orchestration
        result = loop.run_until_complete(
            orchestrate_extraction(
                chapter_id,
                chapter_number,
                chapter_title,
                story_context,
                current_chapter_content,
                word_count
            )
        )
        
        logger.success(
            f"Chapter {chapter_number}: Extraction complete! "
            f"Condensed to {result['condensed_word_count']} words"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chapter {chapter_number} extraction failed: {e}")
        
        # Update task state for progress tracking
        self.update_state(
            state='FAILURE',
            meta={
                'chapter_id': chapter_id,
                'chapter_number': chapter_number,
                'error': str(e),
                'exc_type': type(e).__name__
            }
        )
        
        # Retry on transient failures (API errors, timeouts)
        if isinstance(e, (ConnectionError, TimeoutError)):
            logger.info(f"Retrying Chapter {chapter_number} due to transient error...")
            raise self.retry(exc=e, countdown=60)  # Retry after 1 minute
        
        # Don't retry on permanent failures
        raise