from typing import Any, Dict, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.ai.models.edits import ChapterEdit
from app.ai.edits import generate_line_edits
from app.core.database import get_db
from datetime import datetime
from app.models import Chapter
from loguru import logger
from app.config.celery import celery_app
import asyncio


async def save_line_edits_to_db(
    db: AsyncSession,
    chapter_id: str,
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> Dict[str, Any]:
    try:

        chapter = await db.get(Chapter, chapter_id)

        if not chapter:
            raise ValueError(f"Chapter with ID {chapter_id} does not exist!")
        
        result: ChapterEdit = await generate_line_edits(
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        )

        chapter.line_edits = [edit.model_dump() for edit in result.edits]
        chapter.line_edits_generated_at = datetime.now()

        await db.commit()

        return {
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "status": "success",
            "paragraphs_edited": len(result.edits)
        }
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to generate line edits for chapter {chapter_number}: {e}")
        raise


async def arun_line_edit_job(
    chapter_id: str,
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> Dict[str, Any]:
    async with get_db() as db:
        result = await save_line_edits_to_db(
            db,
            chapter_id,
            story_context,
            current_chapter_content,
            chapter_number,
            chapter_title
        )
        return result
    

@celery_app.task(bind=True, max_retries=3)
def run_line_edit_job(
    self,
    chapter_id: str,
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> Dict[str, Any]:
    try:

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            arun_line_edit_job(
                chapter_id,
                story_context,
                current_chapter_content,
                chapter_number,
                chapter_title
            )
        )

        return result
    
    except Exception as e:

        logger.error(f"Chapter {chapter_number} line edits failed: {e}")
        
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

