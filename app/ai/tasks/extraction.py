from sqlmodel.ext.asyncio.session import AsyncSession
from app.ai.character import extract_characters
from app.ai.plot import extract_plot_information
from app.ai.structure import extract_story_structure
from app.ai.world import extract_world_information
from app.ai.context import synthesize_chapter_context
from app.ai.character_bio import extract_character_bios
from app.ai.plot_thread import extract_plot_threads
from app.ai.world_bible import extract_world_bible
from app.ai.structure_and_pacing import extract_pacing_and_structure
from app.ai.timeline import extract_story_timeline
from app.ai.models.context import CondensedChapterContext
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.world import WorldExtraction
import asyncio
from app.config.celery import celery_app
from app.core.database import get_db
from typing import Any, Callable, Dict, List, Optional, TypedDict, cast
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
    
    # Gather all extraction types
    character_extractions = [ch.character_extraction for ch in chapters]
    plot_extractions = [ch.plot_extraction for ch in chapters]
    world_extractions = [ch.world_extraction for ch in chapters]
    structure_extractions = [ch.structure_extraction for ch in chapters]
    
    # Run ALL 5 story-level extractions in parallel
    async with asyncio.TaskGroup() as tg:
        character_bios_task = tg.create_task(extract_character_bios(
            story_context, character_extractions, story.title, len(chapters)
        ))
        plot_threads_task = tg.create_task(extract_plot_threads(
            story_context, plot_extractions, story.title, len(chapters)
        ))
        world_bible_task = tg.create_task(extract_world_bible(
            story_context, world_extractions, story.title, len(chapters)
        ))
        pacing_structure_task = tg.create_task(extract_pacing_and_structure(
            story_context, structure_extractions, story.title, len(chapters)
        ))
        story_timeline_task = tg.create_task(extract_story_timeline(
            story_context, plot_extractions, story.title, len(chapters)
        ))
    
    # Save all results
    story.character_bios = character_bios_task.result().model_dump()
    story.plot_threads = plot_threads_task.result().model_dump()
    story.world_bible = world_bible_task.result().model_dump()
    story.pacing_structure = pacing_structure_task.result().model_dump()
    story.story_timeline = story_timeline_task.result().model_dump()
    
    logger.info(f"Successfully updated all story bible fields for story: {story_id}")


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
    progress_callback: Optional[Callable[[int, int, int], None]] = None
) -> List[Dict[str, Any]]:
    """
    Re-extract current chapter and ALL subsequent chapters.
    This ensures rolling context propagates changes forward.
    """
    async with cast(AsyncSession, get_db()) as db:
        
        # Get the story
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")
        
        # Get all chapters in order
        chapters = await StoryProvider(db).get_ordered_chapters(
            chapter.user_id, 
            chapter.story_id
        )
        
        # Find chapters from current onwards
        chapters_to_extract = [
            ch for ch in chapters 
            if ch.chapter_number >= chapter_number
        ]
        
        logger.info(
            f"Extracting {len(chapters_to_extract)} chapters "
            f"(from Chapter {chapter_number} onwards)"
        )
        
        results = []
        
        # Build initial context from chapters BEFORE the edited one
        previous_chapters = [ch for ch in chapters if ch.chapter_number < chapter_number]
        accumulated_context = encode({
            "chapters": [
                {"number": i+1, "title": ch.title, "context": ch.condensed_context}
                for i, ch in enumerate(previous_chapters)
            ]
        })
        
        # Extract each chapter sequentially (rolling context)
        for idx, chapter_to_extract in enumerate(chapters_to_extract):

            if progress_callback:
                progress_callback(
                    idx + 1,
                    len(chapters_to_extract),
                    chapter_to_extract.chapter_number
                )

            logger.info(
                f"Extracting Chapter {chapter_to_extract.chapter_number} "
                f"({idx + 1}/{len(chapters_to_extract)})"
            )
            
            # Extract this chapter with accumulated context
            extraction_results = await get_condensed_context(
                chapter_to_extract.id, #type: ignore
                chapter_to_extract.chapter_number,
                chapter_to_extract.title,
                chapter_to_extract.word_count,
                accumulated_context,
                chapter_to_extract.content
            )
            
            # Save to database (but don't commit yet)
            chapter_to_extract.condensed_context = extraction_results["context"].condensed_text
            chapter_to_extract.timeline_context = extraction_results["context"].timeline_context
            chapter_to_extract.themes = extraction_results["context"].themes_present
            chapter_to_extract.emotional_arc = extraction_results["context"].emotional_arc
            chapter_to_extract.last_extracted_at = datetime.now()
            chapter_to_extract.last_extracted_word_count = chapter_to_extract.word_count
            
            chapter_to_extract.character_extraction = extraction_results["character"].model_dump()
            chapter_to_extract.plot_extraction = extraction_results["plot"].model_dump()
            chapter_to_extract.world_extraction = extraction_results["world"].model_dump()
            chapter_to_extract.structure_extraction = extraction_results["structure"].model_dump()
            
            chapter_to_extract.extraction_version = "1.0.0"
            
            await db.flush()  # Make visible for next iteration
            
            # Update accumulated context for next chapter
            # Re-query to get all chapters processed so far
            all_chapters_so_far = [ch for ch in chapters if ch.chapter_number <= chapter_to_extract.chapter_number]
            accumulated_context = encode({
                "chapters": [
                    {"number": i+1, "title": ch.title, "context": ch.condensed_context}
                    for i, ch in enumerate(all_chapters_so_far)
                ]
            })
            
            results.append({
                "chapter_id": chapter_to_extract.id,
                "chapter_number": chapter_to_extract.chapter_number,
                "status": "success"
            })
        
        # After all chapters extracted, update story-level data ONCE
        logger.info("All chapters extracted, updating story-level data...")
        
        story = await db.get(Story, chapter.story_id)
        if not story:
            raise ValueError(f"Story {chapter.story_id} not found")
        
        story.story_context = accumulated_context
        
        # Update story bible fields
        await update_story_bible_fields(
            db, 
            accumulated_context, 
            story.id, # type: ignore
            chapter.user_id
        )
        
        # Commit everything atomically
        await db.commit()
        
        logger.success(
            f"Successfully extracted {len(results)} chapters "
            f"(Chapters {chapter_number}-{chapters_to_extract[-1].chapter_number})"
        )
        
        return results


@celery_app.task(bind=True, max_retries=3) 
def run_context_extraction_job(
    self, 
    chapter_id: str,
    chapter_number: int
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
                progress_callback=lambda current, total, current_chapter: self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': current,
                        'total': total,
                        'chapter': current_chapter,
                        'percent': int((current / total) * 100)
                    }
                )
            )
        )
        
        logger.success(
            f"Chapter {chapter_number}: Extraction complete! "
            f"Condensed to {result['condensed_word_count']} words" # type: ignore
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