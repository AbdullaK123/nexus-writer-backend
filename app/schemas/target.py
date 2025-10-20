from sqlmodel import SQLModel, Field
from pydantic import model_validator
from typing import Optional, List
from app.models import FrequencyType
from datetime import datetime, timezone, timedelta


def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # Convert timezone-aware datetimes to naive UTC; leave naive as-is
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class TargetResponse(SQLModel):
    quota: int = Field(default=0)
    frequency: FrequencyType = Field(default="Daily")
    from_date: datetime = Field(default=datetime.now() - timedelta(days=30))
    to_date: datetime = Field(default=datetime.now())
    story_id: str
    target_id: Optional[str] = None

    @model_validator(mode="after")
    def normalize_and_validate(self):
        # Normalize to naive UTC for consistent serialization
        self.from_date = _to_naive_utc(self.from_date)
        self.to_date = _to_naive_utc(self.to_date)
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
    def normalize_and_validate(self):
        # Normalize if present
        if self.from_date is not None:
            self.from_date = _to_naive_utc(self.from_date)
        if self.to_date is not None:
            self.to_date = _to_naive_utc(self.to_date)
        if self.to_date and self.from_date and self.to_date < self.from_date:
            raise ValueError("to_date must be after from_date")
        return self


class CreateTargetRequest(SQLModel):
    quota: int
    frequency: FrequencyType
    from_date: datetime
    to_date: datetime

    @model_validator(mode="after")
    def normalize_and_validate(self):
        # Normalize incoming datetimes to naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
        self.from_date = _to_naive_utc(self.from_date)
        self.to_date = _to_naive_utc(self.to_date)
        if self.to_date < self.from_date:
            raise ValueError("to_date must be after from_date")
        return self

