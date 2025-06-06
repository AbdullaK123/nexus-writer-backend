from app.core.database import get_db
from app.providers.story import StoryProvider
from app.providers.chapter import ChapterProvider
from app.utils.retry import db_retry
from app.utils.logging import log_background_job
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import engine
from sqlmodel import select
from app.models import Story
from loguru import logger

@log_background_job
@db_retry(max_retries=3)
async def append_chapter_to_path_end(story_id: str, chapter_id: str):
    """Add newly created chapter to end of story path_array"""
    async with AsyncSession(engine) as db:
        story_provider = StoryProvider(db)
        await story_provider.append_to_path_end(story_id, chapter_id)

@log_background_job
@db_retry(max_retries=3)
async def remove_chapter_from_path(story_id: str, chapter_id: str):
    """Remove deleted chapter from story path_array"""
    async with AsyncSession(engine) as db:
        story_provider = StoryProvider(db)
        await story_provider.remove_from_path(story_id, chapter_id)

@log_background_job
@db_retry(max_retries=3)
async def reorder_chapter_path(story_id: str, from_pos: int, to_pos: int):
    """Reorder chapters in story path_array"""
    async with AsyncSession(engine) as db:
        story_provider = StoryProvider(db)
        await story_provider.reorder_path(story_id, from_pos, to_pos)

@log_background_job
@db_retry(max_retries=5)  # More retries for critical operation
async def sync_all_chapter_pointers(story_id: str):
    """Atomically rebuild all chapter prev/next pointers from path_array"""
    async with AsyncSession(engine) as db:
        story_provider = StoryProvider(db)
        chapter_provider = ChapterProvider(db)
        
        # Get story for chapter provider
        story = await db.get(Story, story_id)
        if story:
            await chapter_provider.sync_pointers_from_path(story)

@log_background_job
@db_retry(max_retries=2)
async def update_story_timestamp(story_id: str):
    """Update story.updated_at when chapters change"""
    async with AsyncSession(engine) as db:
        chapter_provider = ChapterProvider(db)
        await chapter_provider._update_story_timestamp(story_id)

# Composite background job for chapter creation
async def handle_chapter_creation(story_id: str, chapter_id: str):
    """Coordinate all background tasks after chapter creation"""
    # Run tasks in sequence for data consistency
    await append_chapter_to_path_end(story_id, chapter_id)
    await sync_all_chapter_pointers(story_id)
    await update_story_timestamp(story_id)

# Composite background job for chapter deletion  
async def handle_chapter_deletion(story_id: str, chapter_id: str):
    """Coordinate all background tasks after chapter deletion"""
    # Run tasks in sequence for data consistency
    await remove_chapter_from_path(story_id, chapter_id)
    await sync_all_chapter_pointers(story_id)
    await update_story_timestamp(story_id)

# Composite background job for chapter reordering
async def handle_chapter_reordering(story_id: str, from_pos: int, to_pos: int):
    """Coordinate all background tasks after chapter reordering"""
    # Run tasks in sequence for data consistency
    await reorder_chapter_path(story_id, from_pos, to_pos)
    await sync_all_chapter_pointers(story_id)
    await update_story_timestamp(story_id)

# Emergency repair job
@log_background_job
@db_retry(max_retries=10)  # Aggressive retries for repair operations
async def emergency_repair_story_pointers(story_id: str):
    """Emergency repair of corrupted pointer chains (manual trigger)"""
    async with AsyncSession(engine) as db:
        chapter_provider = ChapterProvider(db)
        
        # Validate current state
        is_valid = await chapter_provider.validate_pointer_chain(story_id)

        if is_valid:
            logger.info(f"✅ Story {story_id} pointers are already valid")
            return
        
        logger.warning(f"🚨 Detected corrupted pointers for story {story_id}, attempting repair...")
        story = await db.get(Story, story_id)
        if story:
            await chapter_provider.sync_pointers_from_path(story)
                
            # Re-validate after repair
            is_valid_after = await chapter_provider.validate_pointer_chain(story_id)
            if is_valid_after:
                logger.info(f"✅ Successfully repaired pointers for story {story_id}")
                return
            
            logger.warning(f"❌ Failed to repair pointers for story {story_id}")
        
            

# Health check job (can be run periodically)
@log_background_job
async def validate_all_story_pointers(user_id: str = None):
    """Validate pointer integrity across stories (health check)"""
    async with AsyncSession(engine) as db:
        
        query = select(Story).where(Story.user_id == user_id) if user_id else select(Story)
            
        stories = (await db.execute(query)).scalars().all()
        
        chapter_provider = ChapterProvider(db)
        
        corrupted_stories = []
        for story in stories:
            is_valid = await chapter_provider.validate_pointer_chain(story.id)
            if not is_valid:
                corrupted_stories.append(story.id)
                
        if corrupted_stories:
            logger.warning(f"🚨 Found {len(corrupted_stories)} stories with corrupted pointers: {corrupted_stories}")
        else:
            logger.success(f"✅ All {len(stories)} stories have valid pointer chains")
            
        return corrupted_stories