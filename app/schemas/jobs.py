from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4
from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum

def generate_uuid() -> str:
    return str(uuid4())

def datetime_encoder(dt: datetime) -> str:
    return dt.isoformat()

class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"


class JobType(str, Enum):
    EXTRACTION = "extraction"
    REEXTRACTION = "reextraction"
    LINE_EDIT = "line-edit"


class JobQueuedResponse(BaseModel):
    """Response when a job is successfully queued"""
    model_config = ConfigDict(
        json_encoders={
            datetime: datetime_encoder
        }
    )
    
    job_id: str = Field(default_factory=generate_uuid)
    job_name: str
    job_type: JobType
    started_at: datetime = Field(default_factory=datetime.utcnow)
    status: JobStatus = Field(default=JobStatus.QUEUED)
    
    # Extraction-specific metadata
    chapter_id: Optional[str] = Field(default=None)
    chapter_number: Optional[int] = Field(default=None)
    chapters_to_extract: Optional[int] = Field(
        default=None,
        description="Total number of chapters that will be re-extracted"
    )
    
    # Estimated completion
    estimated_duration_seconds: Optional[int] = Field(
        default=None,
        description="Estimated time to complete (seconds)"
    )


class JobStatusResponse(BaseModel):
    """Detailed status response for job polling"""
    job_id: str 
    status: JobStatus
    
    # Timestamps
    queued_at: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Result data (for SUCCESS status)
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Job result data"
    )
    
    # Error info (for FAILURE status)
    error: Optional[str] = Field(default=None)
    
    # Metadata
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status message"
    )