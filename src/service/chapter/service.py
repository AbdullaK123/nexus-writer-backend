import asyncio
from datetime import datetime
from typing import Dict, Optional, List, Sequence, Protocol, Any
from src.data.models import Chapter, Story
from src.data.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse, ChapterEditRequest
)
from src.service.exceptions import NotFoundError, ValidationError, InternalError
from src.shared.utils.html import get_preview_content, get_word_count
from src.service.jobs.chapter import (
    handle_chapter_creation,
    handle_chapter_deletion,
    handle_chapter_reordering
)
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.data.models.ai.edits import ChapterEdit, ChapterEditResponse, LineEdit
from pymongo.asynchronous.database import AsyncDatabase
from tortoise.transactions import in_transaction
from src.infrastructure.utils.retry import retry_mongo


class BackgroundTaskRunner(Protocol):
    def add_task(self, func: Any, *args: Any, **kwargs: Any) -> None: ...


class ChapterService:

    def __init__(self, mongodb: AsyncDatabase, job_service):
        self.mongodb = mongodb
        self.job_service = job_service

    # ========================================
    # CORE CRUD OPERATIONS - SIMPLE & CLEAN
    # ========================================

    async def create(
        self, 
        story_id: str, 
        user_id: str, 
        data: CreateChapterRequest,
        background_tasks: BackgroundTaskRunner
    ) -> ChapterContentResponse:
        """Create new chapter with immediate pointer setup"""

        story = await Story.get_or_none(id=story_id)
        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        try:
            chapter_to_create = await Chapter.create(
                story_id=story_id,
                user_id=user_id,
                title=data.title,
                content=data.content
            )
            
            await handle_chapter_creation(story_id, chapter_to_create.id)

            # Refresh story to get updated path_array
            await story.refresh_from_db()

            if story.path_array and len(story.path_array) > 1:
                previous_chapter_id = story.path_array[-2]
                background_tasks.add_task(
                    self.job_service.queue_extraction_job,
                    user_id,
                    previous_chapter_id
                )
            
            return await self.get_chapter_with_navigation(
                chapter_to_create.id,
                user_id,
                as_html=True
            )
            
        except (NotFoundError, ValidationError, InternalError):
            raise
        except Exception as e:
            log.error("chapter.create_failed", story_id=story_id, user_id=user_id, error=str(e))
            raise InternalError("Something went wrong while creating your chapter. Please try again.")

    async def get_by_id(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get single chapter by ID with user security and story prefetched"""
        return await Chapter.filter(
            user_id=user_id,
            id=chapter_id
        ).prefetch_related('story').first()
    
    @retry_mongo
    async def get_line_edits(
        self,
        user_id: str,
        chapter_id: str
    ) -> ChapterEditResponse:
        """Get line edits from MongoDB only"""
        
        # Verify chapter exists and user owns it
        chapter_exists = await Chapter.filter(
            user_id=user_id,
            id=chapter_id
        ).exists()
        
        if not chapter_exists:
            log.error("chapter.not_found", chapter_id=chapter_id, user_id=user_id)
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        # Get edits from MongoDB
        chapter_edits = await self.mongodb.chapter_edits.find_one({"chapter_id": chapter_id})
        
        if not chapter_edits:
            log.info("chapter.edits_not_ready: returning empty edits", chapter_id=chapter_id)
            return ChapterEditResponse(
                edits=[],
                last_generated_at=None,
                is_stale=False
            )
        
        line_edits = chapter_edits.get("edits", [])
        last_generated_at = chapter_edits.get("last_generated_at")
        is_stale = chapter_edits.get("is_stale", False)

        return ChapterEditResponse(
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

        chapter = await Chapter.filter(
            id=chapter_id,
            user_id=user_id
        ).prefetch_related('story').first()

        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
            
        story_title = chapter.story.title

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
        await chapter.save(update_fields=list(updated_data.keys()))

        return ChapterContentResponse(
            id=chapter.id,
            title=chapter.title,
            content=chapter.content,
            published=chapter.published,
            story_id=chapter.story_id,  # type: ignore[attr-defined]
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,  # type: ignore[attr-defined]
            next_chapter_id=chapter.next_chapter_id  # type: ignore[attr-defined]
        )

    async def delete(
        self, 
        chapter_id: str, 
        user_id: str
    ) -> dict:
        """Delete chapter with pointer cleanup"""

        cancel_result = await self.job_service.cancel_all_jobs(chapter_id=chapter_id)

        if cancel_result['jobs_cancelled'] > 0:
            log.info(
                "chapter.delete: cancelled pending jobs",
                chapter_id=chapter_id,
                jobs_cancelled=cancel_result['jobs_cancelled'],
                job_type=cancel_result['job_type'],
            )
        
        chapter = await Chapter.filter(
            user_id=user_id,
            id=chapter_id
        ).first()
        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        story_id = chapter.story_id  # type: ignore[attr-defined]

        story = await Story.get_or_none(id=story_id)

        if story and story.path_array and len(story.path_array) > 0:
            chapter_idx = story.path_array.index(chapter_id)
            subsequent_chapter_ids = story.path_array[(chapter_idx + 1):]
            queued_result = await self.job_service.queue_reextraction_job(
                chapter_id,
                story_id,
                subsequent_chapter_ids,
                user_id=user_id
            )
            log.info(
                "chapter.delete: queued reextraction for successors",
                chapter_id=chapter_id,
                job_id=queued_result.job_id,
                successor_count=len(subsequent_chapter_ids),
            )
        
        try:
            await chapter.delete()
            await handle_chapter_deletion(story_id, chapter_id)

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
            log.error("chapter.delete_failed", chapter_id=chapter_id, user_id=user_id, error=str(e))
            raise InternalError("Something went wrong while deleting your chapter. Please try again.")

    # ========================================
    # STORY CHAPTER OPERATIONS
    # ========================================

    async def get_story_chapters(self, story_id: str, user_id: str) -> ChapterListResponse:
        """Get all chapters for a story in path_array order"""
        
        # Get story with user check
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        story_path = story.path_array
        story_title = story.title
        story_status = story.status
        story_last_updated = story.updated_at
        
        # Get all chapters for this story
        chapters = await Chapter.filter(
            story_id=story_id,
            user_id=user_id
        )
        
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

        chapter = await Chapter.filter(
            id=chapter_id,
            user_id=user_id
        ).prefetch_related('story').first()
        
        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        story_title = chapter.story.title

        return ChapterContentResponse(
            id=chapter.id,
            title=chapter.title,
            content=chapter.content if as_html else get_preview_content(chapter.content),
            published=chapter.published,
            story_id=chapter.story_id,  # type: ignore[attr-defined]
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,  # type: ignore[attr-defined]
            next_chapter_id=chapter.next_chapter_id  # type: ignore[attr-defined]
        )

    # ========================================
    # REORDERING OPERATIONS
    # ========================================

    async def reorder_chapters(
        self, 
        story_id: str, 
        user_id: str, 
        data: ReorderChapterRequest,
        background_tasks: BackgroundTaskRunner
    ) -> dict:
        """Reorder chapters with pointer updates"""

        cancel_edit_result = await self.job_service.cancel_all_jobs(story_id=story_id, job_type="line-edit")
        cancel_extraction_result = await self.job_service.cancel_all_jobs(story_id=story_id, job_type="extraction")

        if cancel_edit_result['jobs_cancelled'] > 0:
            log.info(
                "chapter.reorder: cancelled jobs",
                story_id=story_id,
                jobs_cancelled=cancel_edit_result['jobs_cancelled'],
                job_type="line-edit",
            )

        if cancel_extraction_result['jobs_cancelled'] > 0:
            log.info(
                "chapter.reorder: cancelled jobs",
                story_id=story_id,
                jobs_cancelled=cancel_extraction_result['jobs_cancelled'],
                job_type="extraction",
            )
        
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        if not story.path_array:
            raise ValidationError(message="This story has no chapters to reorder.")
            
        max_pos = len(story.path_array) - 1
        
        if data.from_pos < 0 or data.from_pos > max_pos:
            raise ValidationError(message=f"Invalid chapter position. Must be between 0 and {max_pos}.")
            
        if data.to_pos < 0 or data.to_pos > max_pos:
            raise ValidationError(message=f"Invalid target position. Must be between 0 and {max_pos}.")
        
        if data.from_pos == data.to_pos:
            return {"message": "No reordering needed"}
        
        try:
            await handle_chapter_reordering(story_id, data.from_pos, data.to_pos)
            await story.refresh_from_db()

            # trigger a reextraction
            new_freshest_chapter_id = story.path_array[(min(data.from_pos, data.to_pos))]
            chapter_ids_to_reextract = story.path_array[min(data.from_pos, data.to_pos):]
            background_tasks.add_task(
                self.job_service.queue_reextraction_job,
                new_freshest_chapter_id,
                story_id,
                chapter_ids_to_reextract,
                user_id=user_id
            )

            return {"message": "Chapters reordered successfully"}
        except Exception as e:
            log.error("chapter.reorder_failed", story_id=story_id, user_id=user_id, error=str(e))
            raise InternalError("Something went wrong while reordering your chapters. Please try again.")

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _get_story_with_user_check(self, story_id: str, user_id: str) -> Optional[Story]:
        """Get story ensuring user ownership"""
        return await Story.filter(
            id=story_id,
            user_id=user_id
        ).first()

