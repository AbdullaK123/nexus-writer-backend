from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, List
from app.models import Chapter, Story
from app.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest, 
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse
)
from fastapi import HTTPException, status, BackgroundTasks

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
    ) -> Chapter:
        """Create new chapter, append to story path, sync pointers"""
        pass

    async def get_by_id(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get single chapter by ID with user security"""
        pass

    async def update(self, chapter_id: str, user_id: str, data: UpdateChapterRequest) -> Chapter:
        """Update chapter content, title, or published status"""
        pass

    async def delete(self, chapter_id: str, user_id: str, background_tasks: BackgroundTasks) -> dict:
        """Delete chapter, remove from path, sync pointers"""
        pass

    # Story Chapter Operations
    async def get_story_chapters(self, story_id: str, user_id: str) -> ChapterListResponse:
        """Get all chapters for a story in path_array order"""
        pass

    async def get_chapter_with_navigation(self, chapter_id: str, user_id: str) -> ChapterContentResponse:
        """Get chapter with prev/next navigation and story context"""
        pass

    # Reordering Operations
    async def reorder_chapters(
        self, 
        story_id: str, 
        user_id: str, 
        data: ReorderChapterRequest, 
        background_tasks: BackgroundTasks
    ) -> dict:
        """Reorder chapters in story, trigger path and pointer sync"""
        pass

    # Background Job Support Methods
    async def sync_pointers_from_path(self, story: Story):
        """Atomically rebuild all chapter pointers from story.path_array (for background jobs)"""
        pass

    async def validate_pointer_chain(self, story_id: str) -> bool:
        """Validate that pointer chain matches path_array (debugging/health checks)"""
        pass

    # Helper Methods
    async def _get_story_with_user_check(self, story_id: str, user_id: str) -> Story:
        """Get story ensuring user ownership (internal helper)"""
        pass

    async def _update_story_timestamp(self, story_id: str):
        """Update story.updated_at when chapters change (for background jobs)"""
        pass

    # Navigation Helpers
    async def get_next_chapter(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get next chapter using pointer navigation"""
        pass

    async def get_prev_chapter(self, chapter_id: str, user_id: str) -> Optional[Chapter]:
        """Get previous chapter using pointer navigation"""
        pass

    # Advanced Operations  
    async def get_chapters_by_published_status(self, story_id: str, user_id: str, published: bool) -> List[Chapter]:
        """Filter chapters by published status"""
        pass

    async def search_chapter_content(self, story_id: str, user_id: str, search_term: str) -> List[Chapter]:
        """Search chapter content within a story"""
        pass