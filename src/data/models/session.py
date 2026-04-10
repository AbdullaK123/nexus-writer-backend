from tortoise import fields
from tortoise.models import Model

from src.data.models.user import TimestampMixin


class Session(Model, TimestampMixin):
    session_id = fields.CharField(max_length=255, pk=True, index=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="sessions", on_delete=fields.CASCADE, index=True
    )
    expires_at = fields.DatetimeField()
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=512, null=True)

    class Meta:
        table = "session"
