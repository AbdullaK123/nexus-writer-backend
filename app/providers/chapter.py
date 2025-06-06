from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, col
from typing import Optional, List
from app.models import Chapter, Story
from datetime import datetime
from app.core.database import get_db
from app.background_jobs.chapter import (
    handle_chapter_creation,
    handle_chapter_deletion
)
from app.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest, 
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse
)
from fastapi import HTTPException, status, BackgroundTasks, Depends

class ChapterProvider:

    def __init__(self, db: AsyncSession):
        self.db = db

    # Core CRUD Operations
    async def create(
        self, 
        story_id: str, 
        user_id: str, 
        data: CreateChapterRequest, 
        background_tasks: BackgroundTasks
    ) -> ChapterContentResponse:
        """Create new chapter, append to story path, sync pointers"""
        chapter_to_create = Chapter(
            story_id=story_id,
            user_id=user_id,
            title=data.title,
            content=data.content
        )
        self.db.add(chapter_to_create)
        await self.db.commit()
        await self.db.refresh(chapter_to_create)
        background_tasks.add_task(handle_chapter_creation, story_id, chapter_to_create.id)
        return ChapterContentResponse(
            id=chapter_to_create.id,
            title=chapter_to_create.title,
            content=chapter_to_create.content,
            story_id=chapter_to_create.story_id,
            story_title=chapter_to_create.story.title,
            created_at=chapter_to_create.created_at,
            updated_at=chapter_to_create.updated_at
        )

    async def get_by_id(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get single chapter by ID with user security"""
        chapter_query = (
            select(Chapter)
            .where(
                Chapter.user_id == user_id,
                Chapter.id == chapter_id
            )
        )
        chapter = (await self.db.execute(chapter_query)).scalar_one_or_none()
        return chapter

    async def update(self, chapter_id: str, user_id: str, data: UpdateChapterRequest) -> ChapterContentResponse:
        """Update chapter content, title, or published status"""
        chapter = await self.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter does not exist"
            )
        updated_data = data.model_dump(exclude_unset=True)
        for field, value in updated_data.items():
            setattr(chapter, field, value)
        await self.db.commit()
        return ChapterContentResponse(
            id=chapter.id,
            title=chapter.title,
            content=chapter.content,
            story_id=chapter.story_id,
            story_title=chapter.story.title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at
        )


    async def delete(self, chapter_id: str, user_id: str, background_tasks: BackgroundTasks) -> dict:
        """Delete chapter, remove from path, sync pointers"""
        chapter = await self.get_by_id(chapter_id, user_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter does not exist"
            )
        story_id = chapter.story_id
        await self.db.delete(chapter)
        await self.db.commit()
        background_tasks.add_task(handle_chapter_deletion, story_id, chapter_id)
        return {
            "message": "Chapter was succesfully deleted"
        }

    # Story Chapter Operations
    async def get_story_chapters(self, story_id: str, user_id: str) -> ChapterListResponse:
        """Get all chapters for a story in path_array order"""
        story = await self._get_story_with_user_check(story_id, user_id)
        story_path = story.path_array
        chapters = story.chapters
        chapters_lookup = {chapter.id : chapter for chapter in chapters}
        chronological_chapters = [
            chapters_lookup[chapter_id]
            for chapter_id in story_path
        ]
        list_items = [
            ChapterListItem(
                id=chapter.id,
                title=chapter.title,
                is_published=chapter.published,
                updated_at=chapter.updated_at
            )
            for chapter in chronological_chapters
        ]
        return ChapterListResponse(
            story_id=story_id,
            story_title=story.title,
            chapters=list_items if chapters else []
        )

    async def get_chapter_with_navigation(self, chapter_id: str, user_id: str) -> ChapterContentResponse:
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
            content=chapter.content,
            story_id=chapter.story_id,
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,
            next_chapter_id=chapter.next_chapter_id
        )
 

    # Reordering Operations
    async def reorder_chapters(
        self, 
        story_id: str, 
        user_id: str, 
        data: ReorderChapterRequest, 
        background_tasks: BackgroundTasks
    ) -> dict:
        """Reorder chapters in story, trigger path and pointer sync"""
        
        # Get story with user check
        story = await self._get_story_with_user_check(story_id, user_id)
        if not story:
            raise HTTPException(404, "Story not found")
        
        # Validate positions against path_array (the source of truth)
        if not story.path_array:
            raise HTTPException(400, "Story has no chapters to reorder")
            
        max_pos = len(story.path_array) - 1
        
        if data.from_pos < 0 or data.from_pos > max_pos:
            raise HTTPException(400, f"from_pos must be between 0 and {max_pos}")
            
        if data.to_pos < 0 or data.to_pos > max_pos:
            raise HTTPException(400, f"to_pos must be between 0 and {max_pos}")
        
        if data.from_pos == data.to_pos:
            return {"message": "No reordering needed"}
        
        # Let background jobs handle ALL the logic
        from app.background_jobs.chapter import handle_chapter_reordering
        background_tasks.add_task(handle_chapter_reordering, story_id, data.from_pos, data.to_pos)
        
        return {"message": "Chapter reordering initiated"}

    # Background Job Support Methods
    async def sync_pointers_from_path(self, story: Story):
        """Atomically rebuild all chapter pointers from story.path_array (for background jobs)"""
        if not story.path_array:
            return # there's nothing to do
        
        chapters_query = select(Chapter).where(Chapter.story_id == story.id)
        chapters = (await self.db.execute(chapters_query)).scalars().all()
        chapters_lookup = {chapter.id : chapter for chapter in chapters}

        for i, chapter_id in enumerate(story.path_array):
            chapter = chapters_lookup[chapter_id]
            chapter.prev_chapter_id = story.path_array[i-1] if i > 0 else None
            chapter.next_chapter_id = story.path_array[i+1] if i < len(story.path_array) - 1 else None

        assert await self._validate_pointer_chain(story.id)

        await self.db.commit()

    async def _validate_pointer_chain(self, story_id: str) -> bool:
        """Validate that pointer chain matches path_array (debugging/health checks)"""
        # get story and its path array
        story = await self.db.get(Story, story_id)
        story_path = story.path_array

        # get its chapters
        chapters_query = select(Chapter).where(Chapter.story_id == story_id)
        chapters = (await self.db.execute(chapters_query)).scalars().all()
        chapters_lookup = {chapter.id: chapter for chapter in chapters}

        # do a forward pass through the chapters, following the pointers to build the chain
        forward_pass_pointer = chapters_lookup[story_path[0]]
        forward_pass = []

        while forward_pass_pointer:
            forward_pass.append(forward_pass_pointer.id)
            forward_pass_pointer = chapters_lookup.get(forward_pass_pointer.next_chapter_id)

         # check if it equals the path array
        if forward_pass != story_path:
            return False

        # do a backward pass through the chapters, following the prev pointers
        backward_pass_pointer = chapters_lookup[story_path[-1]]
        backward_pass = []

        while backward_pass_pointer:
            backward_pass.insert(0, backward_pass_pointer.id)
            backward_pass_pointer = chapters_lookup.get(backward_pass_pointer.prev_chapter_id)

        # check if it equals the path array
        if backward_pass != story_path:
            return False

        # if all checks succeed return true
        return True

    # Helper Methods
    async def _get_story_with_user_check(self, story_id: str, user_id: str) -> Optional[Story]:
        """Get story ensuring user ownership (internal helper)"""
        query = select(Story).where(
            Story.id == story_id,
            Story.user_id == user_id
        )
        return (await self.db.execute(query)).scalar_one_or_none()

    async def _update_story_timestamp(self, story_id: str):
        """Update story.updated_at when chapters change (for background jobs)"""
        story = await self.db.get(Story, story_id)
        if story:
            story.updated_at = datetime.utcnow()
            await self.db.commit()

    # Navigation Helpers
    async def get_next_chapter(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get next chapter using pointer navigation"""
        chapter = await self.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter does not exist"
            )

        next_chapter_id = chapter.next_chapter_id 

        if not next_chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"There is no chapter after chapter: {chapter.title}"
            )
        
        return await self.get_by_id(next_chapter_id, user_id)

    async def get_prev_chapter(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get previous chapter using pointer navigation"""
        chapter = await self.get_by_id(chapter_id, user_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter does not exist"
            )

        prev_chapter_id = chapter.prev_chapter_id 

        if not prev_chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"There is no chapter before chapter: {chapter.title}"
            )
        
        return await self.get_by_id(prev_chapter_id, user_id)

    # Advanced Operations  
    async def get_chapters_by_published_status(self, story_id: str, user_id: str, published: bool) -> List[Chapter]:
        """Filter chapters by published status"""
        chapters_query = (
            select(Chapter)
            .where(
                Chapter.user_id == user_id,
                Chapter.story_id == story_id,
                Chapter.published == published
            )
        )
        chapters = (await self.db.execute(chapters_query)).scalars().all()

    async def search_chapter_content(self, story_id: str, user_id: str, search_term: str) -> List[Chapter]:
        """Search chapter content within a story"""
        query = (
            select(Chapter)
            .where(
                Chapter.story_id == story_id,
                Chapter.user_id == user_id,
                col(Chapter.content).ilike(search_term)
            )
        )
        chapters = (await self.db.execute(query)).scalars().all()
        return chapters


async def get_chapter_provider(db: AsyncSession = Depends(get_db)):
    return ChapterProvider(db)