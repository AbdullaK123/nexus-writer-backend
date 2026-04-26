# mypy: disable-error-code="var-annotated"
from tortoise import fields
from tortoise.models import Model
from src.data.models.enums import generate_uuid, ExtractionType
from src.data.models.user import TimestampMixin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.data.models import Chapter

class Extraction(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    chapter: fields.ForeignKeyRelation["Chapter"] = fields.ForeignKeyField(
        "models.Chapter",
        related_name="extractions",
        on_delete=fields.CASCADE,
        index=True
    )
    chapter_id: str 
    extraction_type = fields.CharEnumField(
        ExtractionType,
        max_length=32
    )
    needs_reextraction = fields.BooleanField(default=False, index=True)
    data = fields.JSONField()

    class Meta:
        table = "extraction"
        unique_together = (("chapter_id", "extraction_type"),)

