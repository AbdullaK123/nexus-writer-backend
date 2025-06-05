from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime

class CreateChapterRequest(SQLModel):
    title: str
    content: str = ""

class UpdateChapterRequest(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

class ReorderChapterRequest(SQLModel):
    from_pos: int
    to_pos: int

class ChapterListItem(SQLModel):
    id: str
    title: str
    is_published: bool
    updated_at: datetime

class ChapterContentResponse(SQLModel):
    id: str
    title: str
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
    chapters: List[ChapterListItem]