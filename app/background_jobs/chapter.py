# app/background_jobs/chapter.py
from app.core.database import engine
from app.utils.retry import db_retry
from app.utils.logging import log_background_job
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from app.models import Story, Chapter
from datetime import datetime
from loguru import logger
from sqlalchemy.orm.attributes import flag_modified

@log_background_job
@db_retry(max_retries=3)
async def append_chapter_to_path_end(story_id: str, chapter_id: str):
    """Add specific chapter to end of story path_array"""
    logger.info(f"🏁 Starting append_chapter_to_path_end: story={story_id}, chapter={chapter_id}")
    
    async with AsyncSession(engine) as db:
        # Get the story
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            raise ValueError(f"Story {story_id} not found")
            
        logger.info(f"📖 Story '{story.title}' current path_array: {story.path_array}")
        
        # Initialize path_array if None
        if story.path_array is None:
            logger.info(f"📝 Initializing empty path_array for story {story_id}")
            story.path_array = []
        
        # Verify chapter exists
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            logger.error(f"❌ Chapter {chapter_id} not found!")
            raise ValueError(f"Chapter {chapter_id} not found")
            
        logger.info(f"📄 Found chapter '{chapter.title}' to add")
        
        # Check if chapter already in path
        if chapter_id in story.path_array:
            logger.warning(f"⚠️  Chapter {chapter_id} already in path_array at position {story.path_array.index(chapter_id)}")
            return
        
        # ✅ Create new list (forces SQLAlchemy change detection)
        new_path = story.path_array.copy()
        new_path.append(chapter_id)
        story.path_array = new_path
        
        # ✅ Explicitly flag as modified for PostgreSQL arrays
        flag_modified(story, 'path_array')
        
        logger.info(f"📝 Added chapter {chapter_id} to path_array: {story.path_array}")
        
        await db.commit()
        logger.success(f"✅ Successfully committed path_array update")
        
        # Verify the change persisted
        await db.refresh(story)
        logger.info(f"📊 Story now has {len(story.path_array)} chapters: {story.path_array}")

@log_background_job
@db_retry(max_retries=3)
async def remove_chapter_from_path(story_id: str, chapter_id: str):
    """Remove deleted chapter from story path_array"""
    logger.info(f"🗑️  Starting remove_chapter_from_path: story={story_id}, chapter={chapter_id}")
    
    async with AsyncSession(engine) as db:
        # Get the story
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return
            
        logger.info(f"📖 Story '{story.title}' current path_array: {story.path_array}")
        
        if not story.path_array:
            logger.warning(f"⚠️  No path_array to remove from in story {story_id}")
            return
            
        if chapter_id not in story.path_array:
            logger.warning(f"⚠️  Chapter {chapter_id} not found in path_array")
            return
            
        chapter_position = story.path_array.index(chapter_id)
        logger.info(f"📍 Found chapter {chapter_id} at position {chapter_position}")
        
        # ✅ Create new list without the chapter (forces change detection)
        new_path = [ch_id for ch_id in story.path_array if ch_id != chapter_id]
        story.path_array = new_path
        
        # ✅ Explicitly flag as modified
        flag_modified(story, 'path_array')
        
        logger.info(f"📝 Removed chapter {chapter_id} from path_array: {story.path_array}")
        
        await db.commit()
        logger.success(f"✅ Successfully committed path_array update")
        
        # Verify the change
        await db.refresh(story)
        logger.info(f"📊 Story now has {len(story.path_array)} chapters: {story.path_array}")

@log_background_job
@db_retry(max_retries=3)
async def reorder_chapter_path(story_id: str, from_pos: int, to_pos: int):
    """Reorder chapters in story path_array"""
    logger.info(f"🔄 Starting reorder_chapter_path: story={story_id}, from={from_pos}, to={to_pos}")
    
    async with AsyncSession(engine) as db:
        # Get the story
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return
            
        logger.info(f"📖 Story '{story.title}' current path_array: {story.path_array}")
        
        if not story.path_array:
            logger.warning(f"⚠️  No chapters to reorder in story {story_id}")
            return
            
        # Validate positions
        max_pos = len(story.path_array) - 1
        if from_pos < 0 or from_pos > max_pos:
            logger.error(f"❌ Invalid from_pos {from_pos}. Must be 0-{max_pos}")
            return
            
        if to_pos < 0 or to_pos > max_pos:
            logger.error(f"❌ Invalid to_pos {to_pos}. Must be 0-{max_pos}")
            return
            
        if from_pos == to_pos:
            logger.info(f"📝 No change needed: from_pos == to_pos ({from_pos})")
            return
            
        moving_chapter = story.path_array[from_pos]
        logger.info(f"🎯 Moving chapter {moving_chapter} from position {from_pos} to {to_pos}")
        
        # ✅ Create new reordered list (forces change detection)
        new_path = story.path_array.copy()
        chapter_id = new_path.pop(from_pos)
        new_path.insert(to_pos, chapter_id)
        story.path_array = new_path
        
        # ✅ Explicitly flag as modified
        flag_modified(story, 'path_array')
        
        logger.info(f"📝 Reordered path_array: {story.path_array}")
        
        await db.commit()
        logger.success(f"✅ Successfully committed path_array reorder")
        
        # Verify the change
        await db.refresh(story)
        logger.info(f"📊 Final path_array: {story.path_array}")

@log_background_job
@db_retry(max_retries=5)
async def sync_all_chapter_pointers(story_id: str):
    """Atomically rebuild all chapter prev/next pointers from path_array"""
    logger.info(f"🔗 Starting sync_all_chapter_pointers for story {story_id}")
    
    async with AsyncSession(engine) as db:
        # Get story
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return
            
        logger.info(f"📖 Story '{story.title}' path_array: {story.path_array}")
        
        if not story.path_array:
            logger.warning(f"⚠️  No chapters to sync pointers for story {story_id}")
            return
            
        # Get all chapters for this story
        chapters_query = select(Chapter).where(Chapter.story_id == story_id)
        chapters = (await db.execute(chapters_query)).scalars().all()
        chapters_lookup = {chapter.id: chapter for chapter in chapters}
        
        logger.info(f"📋 Found {len(chapters)} chapters in database for story")
        
        # Log current pointer state
        for chapter in chapters:
            logger.debug(f"  📄 Chapter {chapter.id} ('{chapter.title}'): prev={chapter.prev_chapter_id}, next={chapter.next_chapter_id}")
        
        # Validate all chapters in path exist
        missing_chapters = []
        for chapter_id in story.path_array:
            if chapter_id not in chapters_lookup:
                missing_chapters.append(chapter_id)
                
        if missing_chapters:
            logger.error(f"❌ Found {len(missing_chapters)} chapters in path_array that don't exist: {missing_chapters}")
            # Remove missing chapters from path
            new_path = [ch_id for ch_id in story.path_array if ch_id in chapters_lookup]
            story.path_array = new_path
            flag_modified(story, 'path_array')
            logger.warning(f"🧹 Cleaned path_array, removed missing chapters: {story.path_array}")
        
        # Sync pointers based on path_array order
        logger.info(f"🔧 Syncing pointers from path_array order...")
        
        for i, chapter_id in enumerate(story.path_array):
            chapter = chapters_lookup[chapter_id]
            
            # Set previous chapter
            prev_chapter_id = story.path_array[i - 1] if i > 0 else None
            # Set next chapter  
            next_chapter_id = story.path_array[i + 1] if i < len(story.path_array) - 1 else None
            
            # Update if changed
            if chapter.prev_chapter_id != prev_chapter_id:
                logger.debug(f"📝 Chapter {chapter_id}: prev {chapter.prev_chapter_id} → {prev_chapter_id}")
                chapter.prev_chapter_id = prev_chapter_id
                
            if chapter.next_chapter_id != next_chapter_id:
                logger.debug(f"📝 Chapter {chapter_id}: next {chapter.next_chapter_id} → {next_chapter_id}")
                chapter.next_chapter_id = next_chapter_id
        
        await db.commit()
        logger.success(f"✅ Pointer sync completed!")
        
        # Verify final state
        await db.refresh(story)
        for chapter in chapters:
            await db.refresh(chapter)
            
        logger.info(f"🔍 Final pointer verification:")
        for i, chapter_id in enumerate(story.path_array):
            chapter = chapters_lookup[chapter_id]
            expected_prev = story.path_array[i - 1] if i > 0 else None
            expected_next = story.path_array[i + 1] if i < len(story.path_array) - 1 else None
            
            logger.debug(f"  ✅ Chapter {chapter_id} ('{chapter.title}'): prev={chapter.prev_chapter_id} (expected: {expected_prev}), next={chapter.next_chapter_id} (expected: {expected_next})")
            

@log_background_job
@db_retry(max_retries=2)
async def update_story_timestamp(story_id: str):
    """Update story.updated_at when chapters change"""
    logger.info(f"⏰ Starting update_story_timestamp for story {story_id}")
    
    async with AsyncSession(engine) as db:
        # Get the story
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return
            
        old_timestamp = story.updated_at
        logger.info(f"📖 Story '{story.title}' current updated_at: {old_timestamp}")
        
        # Update timestamp
        new_timestamp = datetime.utcnow()
        story.updated_at = new_timestamp
        
        await db.commit()
        
        # ✅ Log with the variable, not the model attribute
        logger.success(f"✅ Updated story timestamp: {old_timestamp} → {new_timestamp}")

# Composite workflow functions
async def handle_chapter_creation(story_id: str, chapter_id: str):
    """Coordinate all background tasks after chapter creation"""
    logger.info(f"🚀 Starting handle_chapter_creation workflow: story={story_id}, chapter={chapter_id}")
    
    try:
        logger.info(f"📝 Step 1/3: Appending chapter to path...")
        await append_chapter_to_path_end(story_id, chapter_id)
        
        logger.info(f"🔗 Step 2/3: Syncing chapter pointers...")
        await sync_all_chapter_pointers(story_id)
        
        logger.info(f"⏰ Step 3/3: Updating story timestamp...")
        await update_story_timestamp(story_id)
        
        logger.success(f"🎉 Chapter creation workflow completed: story={story_id}, chapter={chapter_id}")
        
    except Exception as e:
        logger.error(f"💥 Chapter creation workflow failed: story={story_id}, chapter={chapter_id}, error={e}")
        raise

async def handle_chapter_deletion(story_id: str, chapter_id: str):
    """Coordinate all background tasks after chapter deletion"""
    logger.info(f"🗑️  Starting handle_chapter_deletion workflow: story={story_id}, chapter={chapter_id}")
    
    try:
        logger.info(f"📝 Step 1/3: Removing chapter from path...")
        await remove_chapter_from_path(story_id, chapter_id)
        
        logger.info(f"🔗 Step 2/3: Syncing chapter pointers...")
        await sync_all_chapter_pointers(story_id)
        
        logger.info(f"⏰ Step 3/3: Updating story timestamp...")
        await update_story_timestamp(story_id)
        
        logger.success(f"🎉 Chapter deletion workflow completed: story={story_id}, chapter={chapter_id}")
        
    except Exception as e:
        logger.error(f"💥 Chapter deletion workflow failed: story={story_id}, chapter={chapter_id}, error={e}")
        raise

async def handle_chapter_reordering(story_id: str, from_pos: int, to_pos: int):
    """Coordinate all background tasks after chapter reordering"""
    logger.info(f"🔄 Starting handle_chapter_reordering workflow: story={story_id}, from={from_pos}, to={to_pos}")
    
    try:
        logger.info(f"📝 Step 1/3: Reordering chapter path...")
        await reorder_chapter_path(story_id, from_pos, to_pos)
        
        logger.info(f"🔗 Step 2/3: Syncing chapter pointers...")
        await sync_all_chapter_pointers(story_id)
        
        logger.info(f"⏰ Step 3/3: Updating story timestamp...")
        await update_story_timestamp(story_id)
        
        logger.success(f"🎉 Chapter reordering workflow completed: story={story_id}, from={from_pos}, to={to_pos}")
        
    except Exception as e:
        logger.error(f"💥 Chapter reordering workflow failed: story={story_id}, from={from_pos}, to={to_pos}, error={e}")
        raise

# Emergency repair and validation functions
@log_background_job
@db_retry(max_retries=10)
async def emergency_repair_story_pointers(story_id: str):
    """Emergency repair of corrupted pointer chains"""
    logger.warning(f"🚨 Starting emergency_repair_story_pointers for story {story_id}")
    
    async with AsyncSession(engine) as db:
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return
            
        logger.info(f"🔧 Attempting emergency repair for story '{story.title}'")
        
        # Force a complete pointer sync
        await sync_all_chapter_pointers(story_id)
        
        logger.success(f"✅ Emergency repair completed for story {story_id}")

@log_background_job
async def validate_story_pointers(story_id: str):
    """Validate pointer integrity for a single story"""
    logger.info(f"🔍 Validating pointer integrity for story {story_id}")
    
    async with AsyncSession(engine) as db:
        story = await db.get(Story, story_id)
        if not story:
            logger.error(f"❌ Story {story_id} not found!")
            return False
            
        if not story.path_array:
            logger.info(f"✅ Story {story_id} has no chapters - valid by default")
            return True
            
        # Get chapters
        chapters_query = select(Chapter).where(Chapter.story_id == story_id)
        chapters = (await db.execute(chapters_query)).scalars().all()
        chapters_lookup = {chapter.id: chapter for chapter in chapters}
        
        # Validate path_array references existing chapters
        for chapter_id in story.path_array:
            if chapter_id not in chapters_lookup:
                logger.error(f"❌ path_array references non-existent chapter: {chapter_id}")
                return False
        
        # Validate pointer chain
        for i, chapter_id in enumerate(story.path_array):
            chapter = chapters_lookup[chapter_id]
            expected_prev = story.path_array[i - 1] if i > 0 else None
            expected_next = story.path_array[i + 1] if i < len(story.path_array) - 1 else None
            
            if chapter.prev_chapter_id != expected_prev:
                logger.error(f"❌ Chapter {chapter_id} prev pointer mismatch: {chapter.prev_chapter_id} != {expected_prev}")
                return False
                
            if chapter.next_chapter_id != expected_next:
                logger.error(f"❌ Chapter {chapter_id} next pointer mismatch: {chapter.next_chapter_id} != {expected_next}")
                return False
        
        logger.success(f"✅ Story {story_id} has valid pointer chain")
        return True