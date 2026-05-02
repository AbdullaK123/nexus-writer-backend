from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ChatThreadRow(BaseModel):
    id: str 
    user_id: str 
    story_id: str 
    created_at: datetime
    updated_at: datetime


class ChatMessageRow(BaseModel):
    id: str
    thread_id: str 
    user_id: str 
    role: Literal['user', 'assistant', 'system', 'tool']
    sequence: int = Field(default=0, ge=0)
    content: str 
    created_at: datetime
    updated_at: datetime


class ChatToolCallRow(BaseModel):
    id: str 
    message_id: str 
    user_id: str 
    tool_name: str 
    sequence: int = Field(default=0, ge=0)
    arguments: dict 
    result: dict | None = None 
    error: str | None = None 
    created_at: datetime