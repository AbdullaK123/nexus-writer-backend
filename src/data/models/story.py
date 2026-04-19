# mypy: disable-error-code="var-annotated"
from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.postgres.fields import ArrayField
from src.data.models.enums import generate_uuid, StoryStatus
from src.data.models.user import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.models.chapter import Chapter
    from src.data.models.summary import Summary
    from src.data.models.extraction import Extraction
    from src.data.models.job import Job
    from src.data.models.target import Target


class Story(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    user = fields.ForeignKeyField(
        "models.User", related_name="stories", on_delete=fields.CASCADE, index=True
    )
    title = fields.CharField(max_length=255, index=True)
    story_context = fields.TextField(null=True)
    status = fields.CharEnumField(StoryStatus, default=StoryStatus.ONGOING)
    path_array = ArrayField(element_type="text", null=True)

    # Reverse relations
    chapters: fields.ReverseRelation["Chapter"]
    target: fields.ReverseRelation["Target"]
    summaries: fields.ReverseRelation["Summary"]
    extractions: fields.ReverseRelation["Extraction"]
    jobs: fields.ReverseRelation["Job"]

    class Meta:
        table = "story"
        unique_together = (("user_id", "title"),)
