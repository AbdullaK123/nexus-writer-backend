# mypy: disable-error-code="var-annotated"
from tortoise import fields
from tortoise.models import Model
from tortoise.validators import MaxValueValidator, MinValueValidator
from src.data.models.enums import generate_uuid, JobStatus
from src.infrastructure.ai.enums import JobType
from src.data.schemas.job import JobStatusResponse


class Job(Model):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story = fields.ForeignKeyField(
        "models.Story", related_name="jobs", on_delete=fields.CASCADE, index=True
    )
    type = fields.CharEnumField(JobType, max_length=20)
    status = fields.CharEnumField(JobStatus, default=JobStatus.QUEUED, max_length=20)
    started_at = fields.DatetimeField(null=True)
    queued_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    failed_at = fields.DatetimeField(null=True)
    message = fields.TextField(default="")
    params = fields.JSONField(default=dict)
    num_retries = fields.IntField(default=0, validators=[MinValueValidator(0)])
    max_retries = fields.IntField(default=3, validators=[MaxValueValidator(5)])

    class Meta:
        table = "job"
        indexes = (("status", "queued_at"),)


    def to_status_response(self) -> JobStatusResponse:
        return JobStatusResponse(
            job_id=self.id,
            job_status=self.status,
            job_type=self.type,
            message=self.message,
            started_at=self.started_at,
            completed_at=self.completed_at 
        )
