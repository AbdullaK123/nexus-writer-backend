from sqlmodel import SQLModel
from typing import Optional
from app.models import FrequencyType
from datetime import datetime


class UpdateTargetRequest(SQLModel):
    quota: Optional[int] = None
    frequency: Optional[FrequencyType] = None 
    from_date: Optional[datetime] = None 
    to_date: Optional[datetime] = None


class CreateTargetRequest(SQLModel):
    quota: int
    frequency: FrequencyType
    from_date: datetime
    to_date: datetime


class TargetResponse(SQLModel):
    story_id: str
    user_id: str 
    quota: int 
    frequency: FrequencyType 
    from_date: datetime 
    to_date: datetime 