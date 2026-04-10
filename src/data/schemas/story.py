from src.data.models.enums import StoryStatus
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.data.schemas.chapter import ChapterListItem
from src.data.schemas.target import TargetResponse

class CreateStoryRequest(BaseModel):
    title: str

class UpdateStoryRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[StoryStatus] = None

class StoryCardResponse(BaseModel):
    id: str
    latest_chapter_id: Optional[str] = None
    title: str
    status: StoryStatus
    total_chapters: int
    word_count: int
    created_at: datetime
    updated_at: datetime

class StoryListItemResponse(BaseModel):
    id: str
    title: str
    word_count: int
    targets: List[TargetResponse]

class StoryDetailResponse(StoryCardResponse):
    chapters: List['ChapterListItem']

class StoryGridResponse(BaseModel):
    stories: List['StoryCardResponse']
