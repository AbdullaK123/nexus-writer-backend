import asyncio
from typing import Optional, List
from src.data.models import Story, Chapter, StoryStatus, Target
from src.service.target.service import TargetService
from src.data.schemas.chapter import ChapterListItem
from src.service.exceptions import NotFoundError, ConflictError
from src.data.schemas.story import (
    CreateStoryRequest,
    StoryListItemResponse,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse
)
from loguru import logger
from src.shared.utils.html import get_word_count
from pymongo.asynchronous.database import AsyncDatabase

class StoryService:

    def __init__(self, mongodb: AsyncDatabase, target_service: TargetService):
        self.mongodb = mongodb
        self.target_service = target_service
        self.job_service = None  # set by container via wire_circular_deps

    async def append_to_path_end(self, story_id: str, chapter_id: str):

        story = await Story.get_or_none(id=story_id)

        logger.debug(f"Append to path triggered!")
        logger.debug(f"Current path array: {story.path_array}")

        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        if story.path_array is None:
            story.path_array = []

        path = list(story.path_array)
        path.append(chapter_id)
        story.path_array = path

        logger.debug(f"Current path array: {story.path_array}")

        await story.save(update_fields=['path_array'])

    async def remove_from_path(self, story_id: str, chapter_id: str):

        story = await Story.get_or_none(id=story_id)

        if not story or story.path_array is None:
            return 
        
        logger.debug(f"Current path array: {story.path_array}")
        
        path = list(story.path_array)
        path.remove(chapter_id)
        story.path_array = path

        logger.debug(f"Current path array: {story.path_array}")

        await story.save(update_fields=['path_array'])

    async def reorder_path(self, story_id: str, from_pos: int, to_pos: int):

        story = await Story.get_or_none(id=story_id)

        if not story or story.path_array is None:
            raise ValueError(f"Story {story_id} does not have a path array")
        
        if from_pos < 0 or from_pos >= len(story.path_array):
            raise ValueError(f"Invalid from_pos! Must be between 0 and {len(story.path_array) - 1}")
        
        if to_pos < 0 or to_pos >= len(story.path_array):
            raise ValueError(f"Invalid to_pos! Must be between 0 and {len(story.path_array) - 1}")
        
        logger.debug(f"Current path array: {story.path_array}")

        path = list(story.path_array)
        chapter_id = path.pop(from_pos)
        path.insert(to_pos, chapter_id)
        story.path_array = path

        logger.debug(f"Current path array: {story.path_array}")

        await story.save(update_fields=['path_array'])

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
        
        if story.path_array and len(story.path_array) > 0 and update_info.status == StoryStatus.COMPLETE:
            last_chapter_id = story.path_array[-1]
            queue_result = await self.job_service.queue_extraction_job(
                user_id=user_id,
                chapter_id=last_chapter_id,
            )
            logger.info(f"Queued extraction job for last chapter {last_chapter_id} with job ID {queue_result['job_id']} due to story completion")
            
        
        update_data = update_info.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(story, field, value)

        await story.save(update_fields=list(update_data.keys()))

        return {
            "message": "Story successfully updated"
        }


    async def delete(self, user_id: str, story_id: str) -> dict:

        cancel_result = await self.job_service.cancel_all_jobs(story_id=story_id)

        if cancel_result['jobs_cancelled'] > 0:
            logger.info(f"Cancelled all pending or running jobs on story {story_id}")
        
        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise NotFoundError("We couldn't find this story. It may have been deleted.")
        
        await story.delete()

        # delete all extractions and edits related to the story in MongoDB
        await asyncio.gather(
            self.mongodb.chapter_edits.delete_many({"story_id": story_id}),
            self.mongodb.character_extractions.delete_many({"story_id": story_id }),
            self.mongodb.plot_extractions.delete_many({"story_id": story_id}),
            self.mongodb.world_extractions.delete_many({"story_id": story_id}),
            self.mongodb.structure_extractions.delete_many({"story_id": story_id}),
            self.mongodb.chapter_contexts.delete_many({"story_id": story_id}),
            return_exceptions=True
        )

        return {
            "message": "Story successfully deleted"
        }


    async def get_ordered_chapters(self, user_id: str, story_id: str) -> List[Chapter]:

        story = await self.get_by_id(user_id, story_id)
        
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
                updated_at=chapter.updated_at
            )
            for chapter in chapters
        ] if chapters else []

        return StoryDetailResponse(
            id=story_id,
            title=story.title,
            status=story.status,
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
        chapters = {}
        for chapter in all_chapters:
            chapters.setdefault(chapter.story_id, []).append(chapter)
    
        story_cards = [
            StoryCardResponse(
                id=story.id,
                latest_chapter_id=story.path_array[-1] if story.path_array else None,
                title=story.title,
                status=story.status,
                total_chapters=len(chapters.get(story.id, [])),
                word_count=sum(get_word_count(chapter.content) for chapter in chapters.get(story.id, [])),
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
        chapters = {}
        for chapter in all_chapters:
            chapters.setdefault(chapter.story_id, []).append(chapter)

        list_responses = [
            StoryListItemResponse(
                id=story.id,
                title=story.title,
                word_count=sum(get_word_count(chapter.content) for chapter in chapters.get(story.id, [])),
                targets = (await self.target_service.get_all_targets_by_story_id(story.id, user_id))
            )
            for story in stories
        ]

        return list_responses
