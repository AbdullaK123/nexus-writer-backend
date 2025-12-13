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
    QUEUED = "queued"      # ← New: Task in queue, not started yet
    STARTING = "starting"   # ← New: Task initializing
    PROGRESS = "progress"   # ← New: Task running with progress
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"        # ← New: Task failed, retrying


class ExtractionProgress(BaseModel):
    """Progress details for extraction jobs"""
    current: int = Field(description="Current chapter being processed")
    total: int = Field(description="Total chapters to process")
    chapter: int = Field(description="Chapter number being extracted")
    percent: int = Field(ge=0, le=100, description="Completion percentage")
    
    @property
    def is_complete(self) -> bool:
        return self.current >= self.total
    
    @property
    def remaining(self) -> int:
        return self.total - self.current


class JobQueuedResponse(BaseModel):
    """Response when a job is successfully queued"""
    model_config = ConfigDict(
        json_encoders={
            datetime: datetime_encoder
        }
    )
    
    job_id: str = Field(default_factory=generate_uuid)
    job_name: str
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
    
    # Progress tracking (for PROGRESS status)
    progress: Optional[ExtractionProgress] = Field(
        default=None,
        description="Extraction progress details"
    )
    
    # Result data (for SUCCESS status)
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Job result data"
    )
    
    # Error info (for FAILURE status)
    error: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    
    # Retry info (for RETRY status)
    retry_count: Optional[int] = Field(default=None)
    max_retries: Optional[int] = Field(default=None)
    next_retry_at: Optional[datetime] = Field(default=None)
    
    # Metadata
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status message"
    )
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state (done or failed)"""
        return self.status in [JobStatus.SUCCESS, JobStatus.FAILURE]
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status in [JobStatus.STARTING, JobStatus.PROGRESS]
    
    @property
    def estimated_time_remaining(self) -> Optional[int]:
        """Calculate estimated seconds remaining"""
        if not self.progress or not self.started_at:
            return None
        
        if self.progress.is_complete:
            return 0
        
        # Calculate based on average time per chapter
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        if self.progress.current == 0:
            return None
        
        avg_per_chapter = elapsed / self.progress.current
        remaining_chapters = self.progress.remaining
        
        return int(avg_per_chapter * remaining_chapters)
    
class JobListResponse(BaseModel):
    """Response for listing multiple jobs"""
    jobs: List[JobStatusResponse]
    total: int
    page: int = 1
    page_size: int = 10