from typing import Optional

from pydantic import BaseModel
from src.data.models.enums import JobStatus
from src.infrastructure.ai.enums import JobType
from datetime import datetime


class JobDatetimeMixin(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStatusResponse(JobDatetimeMixin):
    job_id: str
    job_status: JobStatus
    job_type: JobType
    message: str