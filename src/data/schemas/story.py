from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from src.data.schemas._base import ApiModel
from src.data.schemas.enums import StoryStatus
from src.data.schemas.chapter import ChapterListItem, ChapterRow


class CreateStoryRequest(ApiModel):
    title: str = Field(min_length=1, max_length=255)


class UpdateStoryRequest(ApiModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[StoryStatus] = None


class StoryRow(BaseModel):
    """One row from the `story` table."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    story_context: Optional[str]
    status: StoryStatus
    path_array: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class StoryPathArrayResponse(ApiModel):
    path_array: Optional[List[str]] = []

class StoryCardResponse(ApiModel):
    story_id: str
    status: StoryStatus
    chapter_number: int
    title: str
    word_count: int
    updated_at: datetime

    @classmethod
    def from_story(cls, story: StoryRow, chapters: List[ChapterRow]) -> "StoryCardResponse":
        return cls(
            story_id=story.id,
            title=story.title,
            status=story.status,
            chapter_number=len(chapters),
            word_count=sum(ch.word_count for ch in chapters),
            updated_at=story.updated_at,
        )


class StoryDetailResponse(ApiModel):
    story_id: str
    status: StoryStatus
    chapter_number: int
    title: str
    word_count: int
    updated_at: datetime
    chapters: List["ChapterListItem"]

    @classmethod
    def from_story(
        cls, story: StoryRow, chapters: List["ChapterListItem"]
    ) -> "StoryDetailResponse":
        return cls(
            story_id=story.id,
            title=story.title,
            status=story.status,
            chapter_number=len(chapters),
            word_count=sum(ch.word_count for ch in chapters),
            updated_at=story.updated_at,
            chapters=chapters,
        )


class StoryGridResponse(ApiModel):
    stories: List["StoryCardResponse"]


class StoryStatsResponse(ApiModel):
    total_words: Optional[int] = 0
    total_chapters: Optional[int] = 0
    total_scenes: Optional[int] = 0
    streak_days: Optional[int] = 0    
