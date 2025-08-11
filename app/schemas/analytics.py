from sqlmodel import SQLModel
from datetime import datetime
from typing import Union
from uuid import UUID
from pydantic import field_validator

class WritingSessionEvent(SQLModel):
    sessionId: str
    storyId: str
    chapterId: str
    userId: str
    timestamp: datetime
    wordCount: int

class WritingSession(SQLModel):
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