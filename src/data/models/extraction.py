# mypy: disable-error-code="var-annotated"
from src.data.models.enums import ExtractionType, generate_uuid
from src.data.models.user import TimestampMixin
from tortoise import fields
from tortoise.models import Model
from tortoise.validators import MinValueValidator


class Extraction(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story = fields.ForeignKeyField(
        "models.Story", related_name="extractions", on_delete=fields.CASCADE, index=True
    )
    type = fields.CharEnumField(ExtractionType, max_length=20)
    is_stale = fields.BooleanField(default=False)
    prompt_version = fields.IntField(default=1, validators=[MinValueValidator(1)])
    data = fields.JSONField()

    class Meta:
        table = "extraction"
        unique_together = (("story_id", "type"),)
