from .character import extract_characters
from .plot import extract_plot_information
from .structure import extract_story_structure
from .world import extract_world_information
from .context import synthesize_chapter_context
import asyncio
from app.config.celery import celery_app
from typing import Optional
from loguru import logger


@celery_app.task(bind=True)
def extract_chapter_context(
    self,
    chapter_id: str,
    chapter_number: int,
    chapter_title: str | None,
    word_count: int,
    story_context: str,
    current_chapter_content: str,
):
    """
    Celery task for multi-pass chapter extraction with parallel processing.
    
    Runs 4 extraction passes concurrently, then synthesizes results.
    """
    
    async def _async_extraction():
        """Inner async function to run concurrent extractions"""
        
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
        
        return final_result
    
    # Run the async function from Celery's sync context
    try:
        logger.info(f"Starting extraction for Chapter {chapter_number} (ID: {chapter_id})")
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async extraction
        result = loop.run_until_complete(_async_extraction())
        
        logger.success(f"Chapter {chapter_number}: Extraction complete!")
        
        # Store result in database
        from app.models.chapter import Chapter
        chapter = Chapter.objects.get(id=chapter_id)
        
        # Save condensed context
        chapter.condensed_context = result.condensed_text
        chapter.timeline_context = result.timeline_context
        chapter.themes = result.themes_present
        chapter.emotional_arc = result.emotional_arc
        chapter.last_extracted_at = datetime.now()
        chapter.last_extracted_word_count = word_count
        chapter.save()
        
        # Store detailed extractions as JSONB
        chapter.character_extraction = character_result.model_dump()
        chapter.plot_extraction = plot_result.model_dump()
        chapter.world_extraction = world_result.model_dump()
        chapter.structure_extraction = structure_result.model_dump()
        chapter.save()
        
        logger.info(f"Chapter {chapter_number}: Saved to database")
        
        return {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "status": "success",
            "condensed_word_count": len(result.condensed_text.split())
        }
        
    except Exception as e:
        logger.error(f"Chapter {chapter_number} extraction failed: {e}")
        
        # Update task state for progress tracking
        self.update_state(
            state='FAILURE',
            meta={
                'chapter_id': chapter_id,
                'chapter_number': chapter_number,
                'error': str(e)
            }
        )
        raise