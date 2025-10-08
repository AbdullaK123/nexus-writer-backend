from sqlmodel import SQLModel
from pydantic import model_validator
from typing import Optional, List
from app.models import FrequencyType
from datetime import datetime


class TargetResponse(SQLModel):
    quota: int
    frequency: FrequencyType
    from_date: datetime
    to_date: datetime
    story_id: str
    target_id: str

    @model_validator(mode="after")
    def to_date_greater_than_from_date(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must be after from_date")
        return self


class TargetListResponse(SQLModel):
    targets: List[TargetResponse]

class UpdateTargetRequest(SQLModel):
    quota: Optional[int] = None
    frequency: Optional[FrequencyType] = None 
    from_date: Optional[datetime] = None 
    to_date: Optional[datetime] = None

    @model_validator(mode="after")
    def to_date_greater_than_from_date(self):
        if self.to_date and self.from_date and self.to_date < self.from_date:
            raise ValueError("to_date must be after from_date")
        return self


class CreateTargetRequest(SQLModel):
    quota: int
    frequency: FrequencyType
    from_date: datetime
    to_date: datetime

    @model_validator(mode="after")
    def to_date_greater_than_from_date(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must be after from_date")
        return self

