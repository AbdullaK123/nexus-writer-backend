from app.models import StoryStatus
from sqlmodel import SQLModel
from typing import List, Optional
from datetime import datetime
from app.schemas.chapter import ChapterListItem

class CreateStoryRequest(SQLModel):
    title: str

class UpdateStoryRequest(SQLModel):
    title: Optional[str] = None
    status: Optional[StoryStatus] = None

class StoryCardResponse(SQLModel):
    id: str
    title: str
    status: StoryStatus
    created_at: datetime
    updated_at: datetime

class StoryDetailResponse(StoryCardResponse):
    chapters: List['ChapterListItem']

class StoryGridResponse(SQLModel):
    stories: List['StoryCardResponse']



