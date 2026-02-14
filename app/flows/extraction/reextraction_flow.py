from prefect import flow
from loguru import logger
from app.flows.extraction.chapter_flow import extract_single_chapter_flow
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import engine
from sqlmodel import select
from app.models import Chapter, Story
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.mongodb import get_mongodb, MongoDB
from app.config.settings import app_config


@flow(name="reextraction-flow")
async def reextract_chapters_flow(story_id: str, chapter_ids: List[str]):
    """Re-extract chapters in sequence after deletion, each with proper accumulated context"""

     # Get MongoDB connection
    await MongoDB.connect(app_config.mongodb_url)
    mongodb = get_mongodb()
    
    async with AsyncSession(engine) as db:
        # Get story
        story = await db.get(Story, story_id)
        if not story or not story.path_array:
            raise ValueError(f"Story {story_id} not found or has no chapters")
        
        logger.info(f"Re-extracting {len(chapter_ids)} chapters in sequence")
        
        # Process each chapter IN ORDER (chapter_ids is already ordered from path_array)
        for idx, chapter_id in enumerate(chapter_ids):
            # Get chapter
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                logger.warning(f"Chapter {chapter_id} not found, skipping")
                continue
            
            chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)
            if chapter_number is None:
                logger.warning(f"Could not determine chapter number for {chapter_id}, skipping")
                continue
            
            # ✅ BUILD ACCUMULATED CONTEXT FROM ALL PREVIOUS CHAPTERS
            accumulated_context = await _build_accumulated_context(
                mongodb=mongodb,
                story=story,
                chapter_number=chapter_number
            )
            
            logger.info(f"Re-extracting Chapter {chapter_number} '{chapter.title}' with {len(accumulated_context)} chars of context")
            
            # Extract with proper context
            await extract_single_chapter_flow(
                chapter_id=chapter.id,
                chapter_number=chapter_number,
                chapter_title=chapter.title,
                word_count=chapter.word_count,
                accumulated_context=accumulated_context,
                content=chapter.content
            )
            
            logger.info(f"✅ Completed re-extraction for Chapter {chapter_number}")
        
        logger.success(f"✅ Re-extraction complete for {len(chapter_ids)} chapters")


async def _build_accumulated_context(
    mongodb,
    story: Story,
    chapter_number: int,
) -> str:
    """Build accumulated context from all previous chapters' condensed contexts"""
    if not story.path_array or chapter_number <= 1:
        return ""
    
    # Get chapter IDs before current chapter
    previous_chapter_ids = story.path_array[:chapter_number - 1]
    if not previous_chapter_ids:
        return ""
    
    # Fetch condensed contexts from MongoDB in order
    contexts = []
    for idx, chapter_id in enumerate(previous_chapter_ids):
        chapter_context = await mongodb.chapter_contexts.find_one({"chapter_id": chapter_id})
        if chapter_context and chapter_context.get("condensed_text"):
            contexts.append(
                f"=== Chapter {idx + 1} ===\n{chapter_context['condensed_text']}"
            )
    
    return "\n\n".join(contexts)