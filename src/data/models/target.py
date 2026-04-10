from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone

from src.data.models.enums import generate_uuid, FrequencyType
from src.data.models.user import TimestampMixin


class Target(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story: fields.ForeignKeyRelation["Story"] = fields.ForeignKeyField(
        "models.Story", related_name="target", on_delete=fields.CASCADE, index=True
    )
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="targets", on_delete=fields.CASCADE, index=True
    )
    quota = fields.IntField(default=0)
    frequency = fields.CharEnumField(FrequencyType, default=FrequencyType.DAILY)
    from_date = fields.DatetimeField(default=lambda: datetime.now(timezone.utc))
    to_date = fields.DatetimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table = "target"
        unique_together = (("story_id", "frequency"),)
