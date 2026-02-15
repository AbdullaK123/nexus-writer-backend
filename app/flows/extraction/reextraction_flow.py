from prefect import flow
from loguru import logger
from app.flows.extraction.chapter_flow import extract_single_chapter_flow
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import engine
from app.models import Chapter, Story
from app.core.mongodb import MongoDB
from app.config.settings import app_config


@flow(name="reextraction-flow")
async def reextract_chapters_flow(story_id: str, chapter_ids: List[str]):
    """Re-extract chapters in sequence after deletion, each with proper accumulated context"""

    await MongoDB.connect(app_config.mongodb_url)
    
    async with AsyncSession(engine) as db:
        # Get story
        story = await db.get(Story, story_id)
        if not story or not story.path_array:
            raise ValueError(f"Story {story_id} not found or has no chapters")
        
        logger.info(f"Re-extracting {len(chapter_ids)} chapters in sequence")
        
        # Process each chapter IN ORDER (chapter_ids is already ordered from path_array)
        for chapter_id in chapter_ids:
            # Get chapter
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                logger.warning(f"Chapter {chapter_id} not found, skipping")
                continue
            
            chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)
            if chapter_number is None:
                logger.warning(f"Could not determine chapter number for {chapter_id}, skipping")
                continue
            
            logger.info(f"Re-extracting Chapter {chapter_number} '{chapter.title}'")
            
            # Extract — predecessor wait + context building happen inside the flow
            await extract_single_chapter_flow(
                chapter_id=chapter.id,
                chapter_number=chapter_number,
                chapter_title=chapter.title,
                word_count=chapter.word_count,
                story_id=story_id,
                story_path_array=story.path_array,
                content=chapter.content
            )
            
            logger.info(f"✅ Completed re-extraction for Chapter {chapter_number}")
        
        logger.success(f"✅ Re-extraction complete for {len(chapter_ids)} chapters")