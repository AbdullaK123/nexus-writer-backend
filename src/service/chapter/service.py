from typing import Optional, List, Tuple
from src.data.models import Chapter, Story
from src.data.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse,
)
from src.service.exceptions import NotFoundError, ValidationError, InternalError
from src.shared.utils.html import get_preview_content, get_word_count
from src.service.chapter.utils import (
    handle_chapter_creation,
    handle_chapter_deletion,
    handle_chapter_reordering
)
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
from src.data.utils.decorators import transaction

log = get_layer_logger(LAYER_SERVICE)


class ChapterService:

    # ========================================
    # CORE CRUD OPERATIONS
    # ========================================

    @transaction
    async def create(
        self, 
        story_id: str, 
        user_id: str, 
        data: CreateChapterRequest,
    ) -> Tuple[str, ChapterContentResponse]:
        """Create new chapter with immediate pointer setup"""

        story = await Story.get_or_none(id=story_id)
        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")

        try:
            chapter_to_create = await Chapter.create(
                story_id=story_id,
                user_id=user_id,
                title=data.title,
                content=data.content,
                word_count=get_word_count(data.content) if data.content else 0,
            )
            
            await handle_chapter_creation(story_id, chapter_to_create.id)
            
            return chapter_to_create.id, await self.get_chapter_with_navigation(
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

    async def update(
        self, 
        chapter_id: str, 
        user_id: str, 
        data: UpdateChapterRequest
    ) -> Tuple[str, ChapterContentResponse]:
        """Update chapter content, title, or published status"""

        chapter = await Chapter.filter(
            id=chapter_id,
            user_id=user_id
        ).prefetch_related('story').first()

        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
            
        story_title = chapter.story.title
        story_id = chapter.story_id #type: ignore[attr-defined]
        
        updated_data = data.model_dump(exclude_unset=True)
        if 'content' in updated_data:
            updated_data['word_count'] = get_word_count(updated_data['content'])
        for field, value in updated_data.items():
            setattr(chapter, field, value)
        await chapter.save(update_fields=list(updated_data.keys()))

        return story_id, ChapterContentResponse(
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

    @transaction
    async def delete(
        self, 
        chapter_id: str, 
        user_id: str
    ) -> Tuple[str, str, dict]:
        """Delete chapter with pointer cleanup"""
        
        chapter = await Chapter.filter(
            user_id=user_id,
            id=chapter_id
        ).first()
        if not chapter:
            raise NotFoundError("We couldn't find this chapter. It may have been deleted.")
        
        story_id = chapter.story_id #type: ignore[attr-defined]
        next_chapter_id = chapter.next_chapter_id # type: ignore[attr-defined]
        
        try:
            await chapter.delete()
            await handle_chapter_deletion(story_id, chapter_id)
            return story_id, next_chapter_id, {"message": "Chapter was successfully deleted"}
            
        except Exception as e:
            log.error("chapter.delete_failed", chapter_id=chapter_id, user_id=user_id, error=str(e))
            raise InternalError("Something went wrong while deleting your chapter. Please try again.")

    # ========================================
    # STORY CHAPTER OPERATIONS
    # ========================================

    async def get_story_chapters(self, story_id: str, user_id: str) -> ChapterListResponse:
        """Get all chapters for a story in path_array order"""
        
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        story_path = story.path_array
        story_title = story.title
        story_status = story.status
        story_last_updated = story.updated_at
        
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
                word_count=chapter.word_count,
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

    @transaction
    async def reorder_chapters(
        self,
        story_id: str,
        user_id: str,
        data: ReorderChapterRequest,
    ) -> dict:
        """Reorder chapters with pointer updates"""
        
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

