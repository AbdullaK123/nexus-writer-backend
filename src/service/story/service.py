from typing import Optional, List
from src.data.models import Story, Chapter, StoryStatus, Target
from src.service.target.service import TargetService
from src.data.schemas.chapter import ChapterListItem
from src.data.schemas.target import TargetResponse
from src.service.exceptions import NotFoundError, ConflictError
from src.data.schemas.story import (
    CreateStoryRequest,
    StoryListItemResponse,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse
)
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)


class StoryService:

    def __init__(self, target_service: TargetService):
        self.target_service = target_service

    async def create(self, user_id: str, story_info: CreateStoryRequest) -> dict:

        story = await self.get_by_title(user_id, story_info.title)

        if story:
            raise ConflictError("You already have a story with this title. Please choose a different one.")
        
        await Story.create(
            user_id=user_id,
            title=story_info.title,
            path_array=[]
        )

        return {
            "message": "Story successfully created"
        }


    async def update(self, user_id: str, story_id: str, update_info: UpdateStoryRequest) -> dict:
        
        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        update_data = update_info.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(story, field, value)

        await story.save(update_fields=list(update_data.keys()))

        return {
            "message": "Story successfully updated"
        }


    async def delete(self, user_id: str, story_id: str) -> dict:
        
        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        await story.delete()

        return {
            "message": "Story successfully deleted"
        }


    async def get_ordered_chapters(self, user_id: str, story_id: str) -> List[Chapter]:

        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("Story not found")
        
        # Get ALL chapters in one query
        all_chapters = await Chapter.filter(
            user_id=user_id,
            story_id=story_id
        ).prefetch_related('story')
        
        if not story.path_array:
            # Fallback: return by creation date
            return sorted(all_chapters, key=lambda c: c.created_at, reverse=True)
        
        # Create lookup dict for efficiency
        chapter_lookup = {chapter.id: chapter for chapter in all_chapters}
        
        # Build ordered list from path_array
        ordered_chapters = []
        for chapter_id in story.path_array:
            if chapter_id in chapter_lookup:
                ordered_chapters.append(chapter_lookup[chapter_id])
        
        return ordered_chapters


    async def get_by_title(self, user_id: str, title: str) -> Optional[Story]:

        return await Story.filter(
            user_id=user_id,
            title=title
        ).first()
    

    async def get_by_id(self, user_id: str, id: str) -> Optional[Story]:

        return await Story.filter(
            user_id=user_id,
            id=id
        ).first()
    
    async def get_story_details(self, user_id: str, story_id: str) -> StoryDetailResponse:

        chapters = await self.get_ordered_chapters(user_id, story_id)

        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("A story with that title does not exist")


        chapter_items = [
            ChapterListItem(
                id=chapter.id,
                title=chapter.title,
                published=chapter.published,
                word_count=chapter.word_count,
                updated_at=chapter.updated_at
            )
            for chapter in chapters
        ] if chapters else []

        return StoryDetailResponse(
            id=story_id,
            title=story.title,
            status=story.status,
            total_chapters=len(chapter_items),
            word_count=sum(c.word_count for c in chapter_items),
            created_at=story.created_at,
            updated_at=story.updated_at,
            chapters=chapter_items
        )
    
    async def get_all_stories(self, user_id: str) -> StoryGridResponse:

        stories = await Story.filter(
            user_id=user_id
        ).order_by('-created_at')

        # Get all chapters for all stories in one query
        story_ids = [story.id for story in stories]
        all_chapters = await Chapter.filter(story_id__in=story_ids)
        
        # Group chapters by story_id
        chapters: dict[str, list[Chapter]] = {}
        for chapter in all_chapters:
            chapters.setdefault(chapter.story_id, []).append(chapter)  # type: ignore[attr-defined]
    
        story_cards = [
            StoryCardResponse(
                id=story.id,
                latest_chapter_id=story.path_array[-1] if story.path_array else None,
                title=story.title,
                status=story.status,
                total_chapters=len(chapters.get(story.id, [])),
                word_count=sum(ch.word_count for ch in chapters.get(story.id, [])),
                created_at=story.created_at,
                updated_at=story.updated_at
            )
            for story in stories
        ] if stories else []

        return StoryGridResponse(stories=story_cards)
    
    async def get_all_story_list_items(self, user_id: str) -> List[StoryListItemResponse]:
        
        stories = await Story.filter(
            user_id=user_id
        ).order_by('-created_at')

        # Get all chapters for all stories in one query
        story_ids = [story.id for story in stories]
        all_chapters = await Chapter.filter(story_id__in=story_ids)
        
        # Group chapters by story_id
        chapters: dict[str, list[Chapter]] = {}
        for chapter in all_chapters:
            chapters.setdefault(chapter.story_id, []).append(chapter)  # type: ignore[attr-defined]

        # Get all targets for all stories in one query (avoid N+1)
        all_targets = await Target.filter(story_id__in=story_ids, user_id=user_id)
        targets_by_story: dict[str, list[TargetResponse]] = {}
        for target in all_targets:
            targets_by_story.setdefault(target.story_id, []).append(  # type: ignore[attr-defined]
                TargetResponse(
                    quota=target.quota,
                    frequency=target.frequency,
                    from_date=target.from_date,
                    to_date=target.to_date,
                    story_id=target.story_id,  # type: ignore[attr-defined]
                    target_id=target.id,
                )
            )

        list_responses = [
            StoryListItemResponse(
                id=story.id,
                title=story.title,
                word_count=sum(ch.word_count for ch in chapters.get(story.id, [])),
                targets=targets_by_story.get(story.id, []),
            )
            for story in stories
        ]

        return list_responses
