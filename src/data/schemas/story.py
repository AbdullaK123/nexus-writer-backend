from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from src.data.models.enums import StoryStatus
from src.data.schemas.chapter import ChapterListItem


class CreateStoryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class UpdateStoryRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[StoryStatus] = None


class StoryCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    latest_chapter_id: Optional[str] = None
    title: str
    status: StoryStatus
    total_chapters: int
    word_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_story(cls, story, chapters: list) -> "StoryCardResponse":
        return cls(
            id=story.id,
            latest_chapter_id=story.path_array[-1] if story.path_array else None,
            title=story.title,
            status=story.status,
            total_chapters=len(chapters),
            word_count=sum(ch.word_count for ch in chapters),
            created_at=story.created_at,
            updated_at=story.updated_at,
        )


class StoryDetailResponse(StoryCardResponse):
    chapters: List["ChapterListItem"]

    @classmethod
    def from_story(
        cls, story, chapter_items: list["ChapterListItem"]
    ) -> "StoryDetailResponse":
        return cls(
            id=story.id,
            latest_chapter_id=story.path_array[-1] if story.path_array else None,
            title=story.title,
            status=story.status,
            total_chapters=len(chapter_items),
            word_count=sum(c.word_count for c in chapter_items),
            created_at=story.created_at,
            updated_at=story.updated_at,
            chapters=chapter_items,
        )


class StoryGridResponse(BaseModel):
    stories: List["StoryCardResponse"]
