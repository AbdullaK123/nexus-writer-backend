# mypy: disable-error-code="var-annotated"
from typing import TYPE_CHECKING

from tortoise import fields
from tortoise.models import Model
from tortoise.validators import MinValueValidator
from src.data.models.enums import generate_uuid
from src.data.models.user import TimestampMixin
from src.infrastructure.ai.prompts import SummaryType

if TYPE_CHECKING:
    from src.data.models.story import Story
    from src.data.models.chapter import Chapter


class Summary(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story: fields.ForeignKeyRelation["Story"] = fields.ForeignKeyField(
        "models.Story", related_name="summaries", on_delete=fields.CASCADE, index=True
    )
    story_id: str
    chapter: fields.ForeignKeyRelation["Chapter"] = fields.ForeignKeyField(
        "models.Chapter", related_name="summaries", on_delete=fields.CASCADE, index=True
    )
    chapter_id: str
    type = fields.CharEnumField(SummaryType, max_length=20)
    is_stale = fields.BooleanField(default=False)
    prompt_version = fields.IntField(default=1, validators=[MinValueValidator(1)])
    content = fields.TextField()

    class Meta:
        table = "summary"
        unique_together = (("story_id", "chapter_id", "type"),)
