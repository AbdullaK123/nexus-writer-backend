# app/sync_jobs/chapter.py - CLEANED UP

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import Story, Chapter
from datetime import datetime
from loguru import logger
from sqlalchemy.orm.attributes import flag_modified

# Pure data manipulation functions - no transaction handling

async def append_chapter_to_path_end(story_id: str, chapter_id: str, db: AsyncSession):
    """Add chapter to end of story path_array"""
    story = await db.get(Story, story_id)
    if not story:
        raise ValueError(f"Story {story_id} not found")
        
    if story.path_array is None:
        story.path_array = []
    
    if chapter_id in story.path_array:
        return
    
    new_path = story.path_array.copy()
    new_path.append(chapter_id)
    story.path_array = new_path
    flag_modified(story, 'path_array')
    
async def remove_chapter_from_path(story_id: str, chapter_id: str, db: AsyncSession):
    """Remove chapter from story path_array"""
    story = await db.get(Story, story_id)
    if not story or not story.path_array:
        return
        
    if chapter_id not in story.path_array:
        return
    
    new_path = [ch_id for ch_id in story.path_array if ch_id != chapter_id]
    story.path_array = new_path
    flag_modified(story, 'path_array')

async def reorder_chapter_path(story_id: str, from_pos: int, to_pos: int, db: AsyncSession):
    """Reorder chapters in story path_array"""
    story = await db.get(Story, story_id)
    if not story or not story.path_array:
        return
        
    if from_pos < 0 or from_pos >= len(story.path_array):
        return
    if to_pos < 0 or to_pos >= len(story.path_array):
        return
    if from_pos == to_pos:
        return
    
    new_path = story.path_array.copy()
    chapter_id = new_path.pop(from_pos)
    new_path.insert(to_pos, chapter_id)
    story.path_array = new_path
    flag_modified(story, 'path_array')

async def sync_all_chapter_pointers(story_id: str, db: AsyncSession):
    """Set prev/next pointers from path_array order"""
    story = await db.get(Story, story_id)
    if not story or not story.path_array:
        return
        
    chapters_query = select(Chapter).where(Chapter.story_id == story_id)
    chapters = (await db.execute(chapters_query)).scalars().all()
    chapters_lookup = {chapter.id: chapter for chapter in chapters}
    
    for i, chapter_id in enumerate(story.path_array):
        if chapter_id in chapters_lookup:
            chapter = chapters_lookup[chapter_id]
            chapter.prev_chapter_id = story.path_array[i-1] if i > 0 else None
            chapter.next_chapter_id = story.path_array[i+1] if i < len(story.path_array) - 1 else None

async def update_story_timestamp(story_id: str, db: AsyncSession):
    """Update story.updated_at"""
    story = await db.get(Story, story_id)
    if story:
        story.updated_at = datetime.utcnow()

# Simple orchestration functions - just call the operations in order

async def handle_chapter_creation(story_id: str, chapter_id: str, db: AsyncSession):
    """Complete chapter creation workflow"""
    await append_chapter_to_path_end(story_id, chapter_id, db)
    await sync_all_chapter_pointers(story_id, db)
    await update_story_timestamp(story_id, db)
    logger.info(f"✅ Chapter {chapter_id} prepared for creation in story {story_id}")

async def handle_chapter_deletion(story_id: str, chapter_id: str, db: AsyncSession):
    """Complete chapter deletion workflow"""
    await remove_chapter_from_path(story_id, chapter_id, db)
    await sync_all_chapter_pointers(story_id, db)
    await update_story_timestamp(story_id, db)
    logger.info(f"🗑️ Chapter {chapter_id} prepared for deletion from story {story_id}")

async def handle_chapter_reordering(story_id: str, from_pos: int, to_pos: int, db: AsyncSession):
    """Complete chapter reordering workflow"""
    await reorder_chapter_path(story_id, from_pos, to_pos, db)
    await sync_all_chapter_pointers(story_id, db)
    await update_story_timestamp(story_id, db)
    logger.info(f"🔄 Chapters prepared for reordering in story {story_id}: {from_pos} → {to_pos}")