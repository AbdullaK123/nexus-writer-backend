from typing import Optional

from pydantic import BaseModel, Field
from src.data.models.enums import JobStatus, JobType
from datetime import datetime

from src.data.models.job import Job


class JobDatetimeMixin(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStatusResponse(JobDatetimeMixin):
    job_id: str
    job_status: JobStatus
    job_type: JobType
    message: str

    @classmethod
    def from_job(cls, job: Job) -> "JobStatusResponse":
        return cls(
            job_id=job.id,
            job_status=job.status,
            job_type=job.type,
            message=job.message,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
