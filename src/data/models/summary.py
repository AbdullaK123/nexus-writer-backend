# mypy: disable-error-code="var-annotated"
from tortoise import fields
from tortoise.models import Model
from tortoise.validators import MinValueValidator
from src.data.models.enums import generate_uuid, SummaryType
from src.data.models.user import TimestampMixin


class Summary(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story = fields.ForeignKeyField(
        "models.Story",
        related_name="summaries",
        on_delete=fields.CASCADE,
        index=True
    )
    chapter = fields.ForeignKeyField(
        "models.Chapter",
        related_name="summaries",
        on_delete=fields.CASCADE,
        index=True
    )
    type = fields.CharEnumField(
        SummaryType,
        max_length=20
    )
    is_stale = fields.BooleanField(
        default=False
    )
    prompt_version = fields.IntField(
        default=1, 
        validators=[MinValueValidator(1)]
    )
    content = fields.TextField()

    class Meta:
        table = "summary"
        unique_together = (("story_id", "chapter_id", "type"),)