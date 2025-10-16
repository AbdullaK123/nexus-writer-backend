from app.models import StoryStatus
from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime
from app.schemas.chapter import ChapterListItem
from app.schemas.target import TargetResponse

class CreateStoryRequest(SQLModel):
    title: str

class UpdateStoryRequest(SQLModel):
    title: Optional[str] = None
    status: Optional[StoryStatus] = None

class StoryCardResponse(SQLModel):
    id: str
    latest_chapter_id: Optional[str] = None
    title: str
    status: StoryStatus
    total_chapters: int
    word_count: int
    created_at: datetime
    updated_at: datetime

class StoryListItemResponse(SQLModel):
    id: str
    title: str
    word_count: int
    targets: List[TargetResponse]

class StoryDetailResponse(StoryCardResponse):
    chapters: List['ChapterListItem']

class StoryGridResponse(SQLModel):
    stories: List['StoryCardResponse']



