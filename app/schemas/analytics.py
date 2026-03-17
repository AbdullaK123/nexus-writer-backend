from pydantic import BaseModel, Field
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from uuid import UUID
from pydantic import field_validator
from app.schemas import TargetResponse


class StoryAnalyticsResponse(BaseModel):
    kpis: Dict[str, Any]
    words_over_time: List[Dict[str, Any]]
    target: Optional[TargetResponse] = None

class WritingSessionEvent(BaseModel):
    sessionId: str
    storyId: str
    chapterId: str
    userId: str
    timestamp: datetime
    wordCount: int

class WritingSession(BaseModel):
    id: Union[str, UUID]
    started: datetime
    ended: datetime
    user_id: Union[str, UUID]
    story_id: Union[str, UUID]
    chapter_id: Union[str, UUID]
    words_written: int
    
    @field_validator('id', 'user_id', 'story_id', 'chapter_id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        """Convert UUID objects to strings for consistency"""
        if isinstance(v, UUID):
            return str(v)
        return v