import asyncio
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from typing import Dict, Optional, List, Sequence
from app.core.redis import get_redis
from app.models import Chapter, Story
from app.core.database import get_db
from app.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse, ChapterEditRequest
)
from fastapi import BackgroundTasks, HTTPException, status, Depends
from app.utils.html import get_preview_content, get_word_count
from app.jobs.chapter import (
    handle_chapter_creation,
    handle_chapter_deletion,
    handle_chapter_reordering
)
from loguru import logger
import time
from app.ai.models.edits import ChapterEdit, LineEdit
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.mongodb import get_mongodb


class ChapterService:

    def __init__(self, db: AsyncSession, mongodb: AsyncIOMotorDatabase):
        self.db = db
        self.mongodb = mongodb
        self._job_service = None

    @property
    def job_service(self):
        if self._job_service is None:
            from app.services.jobs import JobService
            self._job_service = JobService(db=self.db, mongodb=self.mongodb)
        return self._job_service

    # ========================================
    # CORE CRUD OPERATIONS - SIMPLE & CLEAN
    # ========================================

    async def create(
        self, 
        story_id: str, 
        user_id: str, 
        data: CreateChapterRequest
    ) -> ChapterContentResponse:
        """Create new chapter with immediate pointer setup - SINGLE TRANSACTION"""

        story = await self.db.get(Story, story_id)
        if not story:
            raise HTTPException(404, "Story not found")

        if story.path_array and len(story.path_array) > 0:
            previous_chapter_id = story.path_array[-1]
            try:
                queue_result = await self.job_service.queue_extraction_job(
                    user_id=user_id,
                    chapter_id=previous_chapter_id,
                )
                logger.info(f"Queued extraction job for previous chapter {previous_chapter_id} with job ID {queue_result.job_id}")
            except HTTPException as e:
                logger.warning(f"Auto-extraction skipped for chapter {previous_chapter_id}: {e.detail}")

        try:
            # 1. Create the basic chapter (but don't commit yet!)
            chapter_to_create = Chapter(
                story_id=story_id,
                user_id=user_id,
                title=data.title,
                content=data.content
            )
            self.db.add(chapter_to_create)
            await self.db.flush()  # Gets the ID without committing
            
            # 2. Handle path array and pointer updates (still same transaction!)
            await handle_chapter_creation(story_id, chapter_to_create.id, self.db)
            
            # 3. Only commit if EVERYTHING succeeded
            await self.db.commit()
            await self.db.refresh(chapter_to_create)
            
            # 4. Return complete chapter with all pointers set
            return await self.get_chapter_with_navigation(
                chapter_to_create.id,
                user_id,
                as_html=True
            )
            
        except Exception as e:
            await self.db.rollback()  # Rollback everything
            logger.error(f"❌ Failed to create chapter: {e}")
            raise HTTPException(500, "Failed to create chapter")

    async def get_by_id(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get single chapter by ID with user security and story eagerly loaded"""
        
        chapter_query = (
            select(Chapter)
            .where(
                Chapter.user_id == user_id,
                Chapter.id == chapter_id
            )
            .options(selectinload(Chapter.story)) # type: ignore
        )
        chapter = (await self.db.execute(chapter_query)).scalar_one_or_none()
        return chapter
    
    async def get_line_edits(
        self,
        user_id: str,
        chapter_id: str
    ) -> ChapterEdit:
        """Get line edits from MongoDB only"""
        
        # Verify chapter exists and user owns it
        chapter_query = (
            select(Chapter.id)
            .where(
                Chapter.user_id == user_id,
                Chapter.id == chapter_id
            )
        )
        chapter_exists = (await self.db.exec(chapter_query)).first()
        
        if not chapter_exists:
            logger.error(f"Chapter {chapter_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        # Get edits from MongoDB
        chapter_edits = await self.mongodb.chapter_edits.find_one({"chapter_id": chapter_id})
        
        if not chapter_edits:
            logger.info(f"Edits not generated yet for chapter {chapter_id}, returning empty edits")
            return ChapterEdit(
                edits=[],
                last_generated_at=None,
                is_stale=False
            )
        
        line_edits = chapter_edits.get("edits", [])
        last_generated_at = chapter_edits.get("last_generated_at")
        is_stale = chapter_edits.get("is_stale", False)

        return ChapterEdit(
            edits=[
                LineEdit(**edit)
                for edit in line_edits
            ],
            last_generated_at=last_generated_at,
            is_stale=is_stale
        )

    async def update(
        self, 
        chapter_id: str, 
        user_id: str, 
        data: UpdateChapterRequest
    ) -> ChapterContentResponse:
        """Update chapter content, title, or published status"""

        query = (
            select(Story.title, Chapter)
            .join(Chapter)
            .where(
                Chapter.id == chapter_id,
                Chapter.user_id == user_id
            )
        )

        result = (await self.db.execute(query)).first()
        if not result:
            raise HTTPException(404, "Chapter not found")
            
        story_title, chapter = result

        # Mark line edits as stale in MongoDB if content changed
        if data.content and chapter.content != data.content:
            await self.mongodb.chapter_edits.update_one(
                {"chapter_id": chapter_id},
                {"$set": {"is_stale": True}},
                upsert=True
            )
        
        updated_data = data.model_dump(exclude_unset=True)
        for field, value in updated_data.items():
            setattr(chapter, field, value)
        await self.db.commit()

        return ChapterContentResponse(
            id=chapter.id,
            title=chapter.title,
            content=chapter.content,
            published=chapter.published,
            story_id=chapter.story_id,
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,
            next_chapter_id=chapter.next_chapter_id
        )

    async def delete(
        self, 
        chapter_id: str, 
        user_id: str
    ) -> dict:
        """Delete chapter with pointer cleanup - SINGLE TRANSACTION"""
        
        chapter_query = select(Chapter).where(
            Chapter.user_id == user_id,
            Chapter.id == chapter_id
        )
        chapter: Optional[Chapter] = (await self.db.execute(chapter_query)).scalar_one_or_none()
        if not chapter:
            raise HTTPException(404, "Chapter does not exist")
        
        story_id = chapter.story_id

        story = await self.db.get(Story, story_id)

        if story and story.path_array and len(story.path_array) > 0:
            chapter_idx = story.path_array.index(chapter_id)
            subsequent_chapter_ids = story.path_array[(chapter_idx + 1):]
            queued_result = await self.job_service.queue_reextraction_job(
                chapter_id,
                story_id,
                subsequent_chapter_ids
            )
            logger.info(f"Queued reextraction job after chapter {chapter_id} deletion with id {queued_result.job_id}")
        
        try:
            # 1. Delete the chapter (but don't commit yet!)
            await self.db.delete(chapter)
            await self.db.flush()  # Apply deletion without committing
            
            # 2. Clean up pointers and path (still same transaction!)
            await handle_chapter_deletion(story_id, chapter_id, self.db)
            
            # 3. Only commit if EVERYTHING succeeded
            await self.db.commit()

            # delete all chapter extractions and edits related to this chapter in MongoDB
            await asyncio.gather(
                self.mongodb.chapter_edits.delete_one({"chapter_id": chapter_id}),
                self.mongodb.character_extractions.delete_one({"chapter_id": chapter_id}),
                self.mongodb.plot_extractions.delete_one({"chapter_id": chapter_id}),
                self.mongodb.world_extractions.delete_one({"chapter_id": chapter_id}),
                self.mongodb.structure_extractions.delete_one({"chapter_id": chapter_id}),
                self.mongodb.chapter_contexts.delete_one({"chapter_id": chapter_id}),
                return_exceptions=True  # Don't fail if these don't exist or there's an error
            )
            return {"message": "Chapter was successfully deleted"}
            
        except Exception as e:
            await self.db.rollback()  # Rollback everything
            logger.error(f"❌ Failed to delete chapter: {e}")
            raise HTTPException(500, "Failed to delete chapter")

    # ========================================
    # STORY CHAPTER OPERATIONS
    # ========================================

    async def get_story_chapters(self, story_id: str, user_id: str) -> ChapterListResponse:
        """Get all chapters for a story in path_array order"""
        
        # Get story with user check
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise HTTPException(404, "Story not found")
        
        story_path = story.path_array
        story_title = story.title
        story_status = story.status
        story_last_updated = story.updated_at
        
        # Get all chapters for this story
        chapters_query = (
            select(Chapter)
            .where(
                Chapter.story_id == story_id,
                Chapter.user_id == user_id
            )
        )
        chapters = (await self.db.execute(chapters_query)).scalars().all()
        
        if not story_path or not chapters:
            return ChapterListResponse(
                story_id=story_id,
                story_title=story_title,
                story_status=story_status,
                story_last_updated=story_last_updated,
                chapters=[]
            )
        
        # Create lookup and order by path_array
        chapters_lookup = {chapter.id: chapter for chapter in chapters}
        chronological_chapters = [
            chapters_lookup[chapter_id]
            for chapter_id in story_path
            if chapter_id in chapters_lookup
        ]
        
        list_items = [
            ChapterListItem(
                id=chapter.id,
                title=chapter.title,
                published=chapter.published,
                word_count=get_word_count(chapter.content),
                updated_at=chapter.updated_at
            )
            for chapter in chronological_chapters
        ]

        return ChapterListResponse(
            story_id=story_id,
            story_title=story_title,
            story_status=story_status,
            story_last_updated=story_last_updated,
            chapters=list_items
        )

    async def get_chapter_with_navigation(
        self, 
        chapter_id: str, 
        user_id: str, 
        as_html: bool = True
    ) -> ChapterContentResponse:
        """Get chapter with prev/next navigation and story context"""

        query = (
            select(Chapter, Story.title)
            .join(Story)
            .where(
                Chapter.id == chapter_id,
                Chapter.user_id == user_id
            )
        )
        
        result = (await self.db.execute(query)).first()
        if not result:
            raise HTTPException(404, "Chapter not found")
        
        chapter, story_title = result

        return ChapterContentResponse(
            id=chapter.id,
            title=chapter.title,
            content=chapter.content if as_html else get_preview_content(chapter.content),
            published=chapter.published,
            story_id=chapter.story_id,
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,
            next_chapter_id=chapter.next_chapter_id
        )

    # ========================================
    # REORDERING OPERATIONS
    # ========================================

    async def reorder_chapters(
        self, 
        story_id: str, 
        user_id: str, 
        data: ReorderChapterRequest
    ) -> dict:
        """Reorder chapters with pointer updates - SINGLE TRANSACTION"""
        
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise HTTPException(404, "Story not found")
        
        if not story.path_array:
            raise HTTPException(400, "Story has no chapters to reorder")
            
        max_pos = len(story.path_array) - 1
        
        if data.from_pos < 0 or data.from_pos > max_pos:
            raise HTTPException(400, f"from_pos must be between 0 and {max_pos}")
            
        if data.to_pos < 0 or data.to_pos > max_pos:
            raise HTTPException(400, f"to_pos must be between 0 and {max_pos}")
        
        if data.from_pos == data.to_pos:
            return {"message": "No reordering needed"}
        
        try:
            await handle_chapter_reordering(story_id, data.from_pos, data.to_pos, self.db)
            await self.db.commit()
            return {"message": "Chapters reordered successfully"}
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to reorder chapters: {e}")
            raise HTTPException(500, "Failed to reorder chapters")

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _get_story_with_user_check(self, story_id: str, user_id: str) -> Optional[Story]:
        """Get story ensuring user ownership"""
        query = select(Story).where(
            Story.id == story_id,
            Story.user_id == user_id
        )
        return (await self.db.execute(query)).scalar_one_or_none()


# Simple dependency - no Redis needed!
async def get_chapter_service(
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    return ChapterService(db, mongodb)