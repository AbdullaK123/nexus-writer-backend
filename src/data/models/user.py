from tortoise import fields
from tortoise.models import Model

from src.data.models.enums import generate_uuid


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class User(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    username = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    profile_img = fields.CharField(max_length=512, null=True, unique=True)

    # Reverse relations
    sessions: fields.ReverseRelation["Session"]
    stories: fields.ReverseRelation["Story"]
    chapters: fields.ReverseRelation["Chapter"]
    targets: fields.ReverseRelation["Target"]

    class Meta:
        table = "user"
