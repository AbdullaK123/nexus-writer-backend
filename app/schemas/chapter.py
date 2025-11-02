from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime
from app.models import StoryStatus

class CreateChapterRequest(SQLModel):
    title: str
    content: str = ""

class UpdateChapterRequest(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published: Optional[bool] = None

class ReorderChapterRequest(SQLModel):
    from_pos: int
    to_pos: int

class ChapterListItem(SQLModel):
    id: str
    title: str
    published: bool
    word_count: int
    updated_at: datetime

class ChapterContentResponse(SQLModel):
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

class ChapterListResponse(SQLModel):
    story_id: str
    story_title: str
    story_status: StoryStatus
    story_last_updated: datetime
    chapters: List[ChapterListItem]

class ChapterEditRequest(SQLModel):
    content: str