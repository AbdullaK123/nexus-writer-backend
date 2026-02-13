import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from typing import Optional, List
from app.models import Story, Chapter, Target
from app.providers.target import TargetProvider
from sqlalchemy.orm import selectinload
from app.schemas.chapter import ChapterListItem
from fastapi import HTTPException, status, Depends
from app.core.database import get_db
from app.schemas.story import (
    CreateStoryRequest,
    StoryListItemResponse,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse
)
from loguru import logger
from app.utils.html import get_word_count
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.mongodb import get_mongodb

class StoryProvider:

    def __init__(self, db: AsyncSession, mongodb: AsyncIOMotorDatabase):
        self.db = db
        self.target_provider = TargetProvider(db)
        self.mongodb = mongodb

    async def append_to_path_end(self, story_id: str, chapter_id: str):

        story = await self.db.get(Story, story_id)

        logger.debug(f"Append to path triggered!")
        logger.debug(f"Current path array: {story.path_array}")

        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        if story.path_array is None:
            story.path_array = []

        story.path_array.append(chapter_id)

        logger.debug(f"Current path array: {story.path_array}")

        await self.db.commit()

    async def remove_from_path(self, story_id: str, chapter_id: str):

        story = await self.db.get(Story, story_id)

        if not story or story.path_array is None:
            return 
        
        logger.debug(f"Current path array: {story.path_array}")
        
        story.path_array.remove(chapter_id)

        logger.debug(f"Current path array: {story.path_array}")

        await self.db.commit()

    async def reorder_path(self, story_id: str, from_pos: int, to_pos: int):

        story = await self.db.get(Story, story_id)

        if not story or story.path_array is None:
            raise ValueError(f"Story {story_id} does not have a path array")
        
        if from_pos < 0 or from_pos >= len(story.path_array):
            raise ValueError(f"Invalid from_pos! Must be between 0 and {len(story.path_array) - 1}")
        
        if to_pos < 0 or to_pos >= len(story.path_array):
            raise ValueError(f"Invalid to_pos! Must be between 0 and {len(story.path_array) - 1}")
        
        logger.debug(f"Current path array: {story.path_array}")

        chapter_id = story.path_array.pop(from_pos)
        story.path_array.insert(to_pos, chapter_id)

        logger.debug(f"Current path array: {story.path_array}")

        await self.db.commit()

    async def create(self, user_id: str, story_info: CreateStoryRequest) -> dict:

        story = await self.get_by_title(user_id, story_info.title)

        if story:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A story with that title already exists"
            )
        
        story_to_add = Story(
            user_id=user_id,
            title=story_info.title,
            path_array=[]
        )

        self.db.add(story_to_add)
        await self.db.commit()
        await self.db.refresh(story_to_add)

        return {
            "message": "Story successfully created"
        }


    async def update(self, user_id: str, story_id: str, update_info: UpdateStoryRequest) -> dict:
        
        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story does not exist"
            )
        
        update_data = update_info.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(story, field, value)

        await self.db.commit()
        await self.db.refresh(story)

        return {
            "message": "Story successfully updated"
        }


    async def delete(self, user_id: str, story_id: str) -> dict:
        
        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story does not exist"
            )
        
        await self.db.delete(story)
        await self.db.commit()

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
        chapter_query = (
            select(Chapter)
            .where(
                Chapter.user_id == user_id,
                Chapter.story_id == story_id
            )
            .options(selectinload(Chapter.story))
        )
        
        all_chapters = (await self.db.execute(chapter_query)).scalars().all()
        
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

        query = (
            select(Story)
            .where(
                Story.user_id == user_id, 
                Story.title == title
            )
        )

        story = (await self.db.execute(query)).scalar_one_or_none()

        return story
    

    async def get_by_id(self, user_id: str, id: str) -> Optional[Story]:

        print(f"DEBUG StoryProvider.get_by_id: story_id={id}, user_id={user_id}")

        query = (
            select(Story)
            .where(
                Story.user_id == user_id, 
                Story.id == id
            )
        )

        story = (await self.db.execute(query)).scalar_one_or_none()

        return story
    
    async def get_story_details(self, user_id: str, story_id: str) -> StoryDetailResponse:

        chapters = await self.get_ordered_chapters(user_id, story_id)

        story = await self.get_by_id(user_id, story_id)

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A story with that title does not exist"
            )


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

        stories_query = (
            select(Story)
            .where(
                Story.user_id == user_id
            )
            .order_by(
                desc(Story.created_at) # default ordering
            )
        )

        stories = (await self.db.execute(stories_query)).scalars().all()

        chapter_queries = {
            story.id: (
                select(Chapter)
                .where(
                    Chapter.story_id == story.id
                ).order_by(
                    desc(Chapter.created_at)
                )
            )
            for story in stories
        }

        chapters = {
            story_id: (await self.db.execute(query)).scalars().all()
            for story_id, query
            in chapter_queries.items()
        }
    
        story_cards = [
            StoryCardResponse(
                id=story.id,
                latest_chapter_id=story.path_array[-1] if story.path_array else None,
                title=story.title,
                status=story.status,
                total_chapters=len(chapters[story.id]),
                word_count=sum(get_word_count(chapter.content) for chapter in chapters[story.id]),
                created_at=story.created_at,
                updated_at=story.updated_at
            )
            for story in stories
        ] if stories else []

        return StoryGridResponse(stories=story_cards)
    
    async def get_all_story_list_items(self, user_id: str) -> List[StoryListItemResponse]:
        
        stories_query = (
            select(Story)
            .where(Story.user_id == user_id)
            .order_by(
                desc(Story.created_at)
            )
        )

        stories = (await self.db.execute(stories_query)).scalars().all()

        chapter_queries = {
            story.id: (
                select(Chapter)
                .where(
                    Chapter.story_id == story.id
                ).order_by(
                    desc(Chapter.created_at)
                )
            )
            for story in stories
        }

        chapters = {
            story_id: (await self.db.execute(query)).scalars().all()
            for story_id, query
            in chapter_queries.items()
        }

        list_responses = [
            StoryListItemResponse(
                id=story.id,
                title=story.title,
                word_count=sum(get_word_count(chapter.content) for chapter in chapters[story.id]),
                targets = (await self.target_provider.get_all_targets_by_story_id(story.id, user_id))
            )
            for story in stories
        ]

        return list_responses
    

async def get_story_provider(
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    return StoryProvider(db, mongodb)