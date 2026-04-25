from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from src.data.models.enums import StoryStatus


class CreateChapterRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = ""


class UpdateChapterRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = None
    published: Optional[bool] = None


class ReorderChapterRequest(BaseModel):
    from_pos: int
    to_pos: int


class ChapterListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    published: bool
    word_count: int
    updated_at: datetime


class ChapterContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    published: bool
    content: str
    story_id: str
    story_title: str
    created_at: datetime
    updated_at: datetime
    previous_chapter_id: Optional[str] = None
    next_chapter_id: Optional[str] = None

    @classmethod
    def from_chapter(
        cls, chapter, *, content: Optional[str] = None
    ) -> "ChapterContentResponse":
        return cls(
            id=chapter.id,
            title=chapter.title,
            published=chapter.published,
            content=chapter.content if content is None else content,
            story_id=chapter.story_id,
            story_title=chapter.story.title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,
            next_chapter_id=chapter.next_chapter_id,
        )


class ChapterListResponse(BaseModel):
    story_id: str
    story_title: str
    story_status: StoryStatus
    story_last_updated: datetime
    chapters: List[ChapterListItem]

    @classmethod
    def from_story(
        cls, story, chapters: List[ChapterListItem]
    ) -> "ChapterListResponse":
        return cls(
            story_id=story.id,
            story_title=story.title,
            story_status=story.status,
            story_last_updated=story.updated_at,
            chapters=chapters,
        )
