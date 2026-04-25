from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields
from tortoise.models import Model

from src.data.models.enums import generate_uuid

if TYPE_CHECKING:
    from src.data.models.chapter import Chapter
    from src.data.models.session import Session
    from src.data.models.story import Story


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class User(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    username = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    profile_img = fields.CharField(max_length=512, null=True)

    # Reverse relations
    sessions: fields.ReverseRelation["Session"]
    stories: fields.ReverseRelation["Story"]
    chapters: fields.ReverseRelation["Chapter"]

    class Meta:
        table = "user"
