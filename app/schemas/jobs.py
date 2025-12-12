from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4
from typing import Optional, Any
from datetime import datetime
from enum import Enum

def generate_uuid() -> str:
    return str(uuid4())

def datetime_encoder(dt: datetime) -> str:
    return dt.isoformat()

class JobStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    
class JobQueuedResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: datetime_encoder
        }
    )
    job_id: str = Field(default_factory=generate_uuid)
    job_name: str
    started_at: datetime
    status: JobStatus = Field(default=JobStatus.STARTED)

class JobStatusResponse(BaseModel):
    job_id: str 
    status: JobStatus
    info: Any


