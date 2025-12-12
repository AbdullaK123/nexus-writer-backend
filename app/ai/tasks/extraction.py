from sqlmodel.ext.asyncio.session import AsyncSession
from app.ai.character import extract_characters
from app.ai.plot import extract_plot_information
from app.ai.structure import extract_story_structure
from app.ai.world import extract_world_information
from app.ai.context import synthesize_chapter_context
from app.ai.character_bio import extract_character_bios
from app.ai.plot_thread import extract_plot_threads
from app.ai.world_bible import extract_world_bible
from app.ai.models.context import CondensedChapterContext
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.world import WorldExtraction
import asyncio
from app.config.celery import celery_app
from app.core.database import get_db
from typing import Any, Dict, List, Optional, TypedDict
from loguru import logger
from datetime import datetime
from app.models import Story, Chapter
from app.providers.story import StoryProvider
from toon import encode


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

async def update_story_context(
    db: AsyncSession,
    user_id: str,
    story_id: str
) -> str:
    
    chapters = await StoryProvider(db).get_ordered_chapters(user_id, story_id)

    story_context = encode({
        "chapters": [
            {"number": i+1, "title": ch.title, "context": ch.condensed_context}
            for i, ch in enumerate(chapters)
        ]
    })


    story = await db.get(Story, story_id)

    if not story:
        raise ValueError(f"Story with id: {story_id} does not exist!")

    story.story_context = story_context

    logger.info(f"Successfully updated story context for story: {story_id}")

    return story_context


async def update_story_bible_fields(
    db: AsyncSession,
    story_context: str,
    story_id: str,
    user_id: str
):

    story = await db.get(Story, story_id)

    if not story:
        raise ValueError(f"Story with id: {story_id} does not exist!")
    
    chapters = await StoryProvider(db).get_ordered_chapters(user_id, story_id)
    character_extractions = [
        chapter.character_extraction
        for chapter in chapters
    ]
    plot_extractions = [
        chapter.plot_extraction
        for chapter in chapters
    ]
    world_extractions = [
        chapter.world_extraction
        for chapter in chapters
    ]

    async with asyncio.TaskGroup() as tg:
        character_bios_task = tg.create_task(extract_character_bios(
            story_context,
            character_extractions,
            story.title,
            len(chapters)
        ))
        plot_threads_task = tg.create_task(extract_plot_threads(
            story_context,
            plot_extractions,
            story.title,
            len(chapters)
        ))
        world_bible_task = tg.create_task(extract_world_bible(
            story_context,
            world_extractions,
            story.title,
            len(chapters)
        ))

    story.character_bios = character_bios_task.result().model_dump()
    story.plot_threads = plot_threads_task.result().model_dump()
    story.world_bible = world_bible_task.result().model_dump()

    logger.info(f"Successfully updated character bios for story: {story_id}")


async def save_extraction_results_to_db(
    db: AsyncSession,
    chapter_id: str,
    chapter_number: int,
    word_count: int,
    extraction_results: ExtractionResults
) -> Dict[str, Any]:
    """Save extraction results to database"""

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

        #update story_context
        await db.flush()   

        story_context = await update_story_context(db, chapter.user_id, chapter.story_id)

        await update_story_bible_fields(db, story_context, chapter.story_id, chapter.user_id)

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
    async with get_db() as db:  # type: ignore
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
def run_context_extraction_job(
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
            raise self.retry(exc=e, countdown=60)   # Retry after 1 minute
        
        # Don't retry on permanent failures
        raise