from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4
from typing import Generic, Optional, Any, Dict, TypeVar
from datetime import datetime, timezone
from enum import Enum

def generate_uuid() -> str:
    return str(uuid4())

def datetime_encoder(dt: datetime) -> str:
    return dt.isoformat()

def get_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)

T = TypeVar("T", bound=BaseModel)

class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"


class FlowEventType(str, Enum):
    TASK_STARTED  = "task_started"
    TASK_FAILED   = "task_failed"
    TASK_COMPLETE = "task_complete"
    FLOW_STARTED  = "flow_started"
    FLOW_FAILED   = "flow_failed"
    FLOW_COMPLETE = "flow_complete"


class JobType(str, Enum):
    EXTRACTION   = "extraction"
    REEXTRACTION = "reextraction"
    LINE_EDIT    = "line-edit"


# ── Flow event data payloads ─────────────────────────────────────────────

class ChapterStartedData(BaseModel):
    chapter_id: str
    chapter_number: int

class EditsGeneratedData(BaseModel):
    edits_count: int

class LineEditsCompleteData(BaseModel):
    chapter_id: str
    chapter_number: int
    edits_count: int

class ExtractionCompleteData(BaseModel):
    chapter_id: str
    chapter_number: int
    is_partial: bool = False
    failed_extractions: list[str] = Field(default_factory=list)

class ExtractionCountData(BaseModel):
    count: int

class ReextractionProgressData(BaseModel):
    chapter_id: str
    chapter_number: int
    is_partial: bool = False

class ReextractionCompleteData(BaseModel):
    chapters_processed: int


# ── Per-flow payload unions ───────────────────────────────────────────

LineEditsEventData = ChapterStartedData | EditsGeneratedData | LineEditsCompleteData

ExtractionEventData = ChapterStartedData | ExtractionCompleteData | ExtractionCountData

ReextractionEventData = ChapterStartedData | ReextractionProgressData | ReextractionCompleteData


class FlowEvent(Generic[T], BaseModel):
    job_run_id: str
    user_id: str
    story_id: str
    event_type: FlowEventType
    job_type: JobType
    trace_id: Optional[str] = None
    task: Optional[str] = None
    data: Optional[T] = None
    message: Optional[str] = None
    step: Optional[int] = None
    total_steps: Optional[int] = None
    duration_ms: Optional[int] = None   # ← add back
    timestamp: datetime = Field(default_factory=get_now)


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
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
