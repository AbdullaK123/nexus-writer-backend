from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.postgres.fields import ArrayField

from src.data.models.enums import generate_uuid, StoryStatus
from src.data.models.user import TimestampMixin


class Story(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="stories", on_delete=fields.CASCADE, index=True
    )
    title = fields.CharField(max_length=255, index=True)
    story_context = fields.TextField(null=True)
    status = fields.CharEnumField(StoryStatus, default=StoryStatus.ONGOING)
    path_array = ArrayField(element_type="text", null=True)

    # Reverse relations
    chapters: fields.ReverseRelation["Chapter"]
    target: fields.ReverseRelation["Target"]

    class Meta:
        table = "story"
        unique_together = (("user_id", "title"),)
