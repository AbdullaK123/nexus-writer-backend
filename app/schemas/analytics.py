from sqlmodel import SQLModel
from datetime import datetime

class WritingSessionEvent(SQLModel):
    sessionId: str
    storyId: str
    chapterId: str
    userId: str
    timestamp: datetime
    wordCount: int


class WritingSession(SQLModel):
    id: str
    started: datetime
    ended: datetime
    user_id: str 
    story_id: str 
    chapter_id: str 
    words_written: int 
