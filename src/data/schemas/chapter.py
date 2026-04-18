from pydantic import BaseModel, Field
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
    id: str
    title: str
    published: bool
    word_count: int
    updated_at: datetime

class ChapterContentResponse(BaseModel):
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

class ChapterListResponse(BaseModel):
    story_id: str
    story_title: str
    story_status: StoryStatus
    story_last_updated: datetime
    chapters: List[ChapterListItem]
