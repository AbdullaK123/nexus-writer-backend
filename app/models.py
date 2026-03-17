from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.postgres.fields import ArrayField
from datetime import datetime
from typing import Optional, List
import uuid
from enum import Enum


def generate_uuid():
    return str(uuid.uuid4())

class StoryStatus(str, Enum):
    COMPLETE = "Complete"
    ON_HAITUS = "On Hiatus"
    ONGOING = "Ongoing"

class FrequencyType(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Session(Model, TimestampMixin):
    session_id = fields.CharField(max_length=255, pk=True, index=True)
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='sessions', on_delete=fields.CASCADE, index=True
    )
    expires_at = fields.DatetimeField()
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=512, null=True)

    class Meta:
        table = "session"


class User(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    username = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    profile_img = fields.CharField(max_length=512, null=True, unique=True)

    # Reverse relations (populated by ForeignKeyField on the other side)
    sessions: fields.ReverseRelation['Session']
    stories: fields.ReverseRelation['Story']
    chapters: fields.ReverseRelation['Chapter']
    targets: fields.ReverseRelation['Target']

    class Meta:
        table = "user"


class Story(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='stories', on_delete=fields.CASCADE, index=True
    )
    title = fields.CharField(max_length=255, index=True)
    story_context = fields.TextField(null=True)
    status = fields.CharEnumField(StoryStatus, default=StoryStatus.ONGOING)
    path_array = ArrayField(element_type="text", null=True)

    # Reverse relations
    chapters: fields.ReverseRelation['Chapter']
    target: fields.ReverseRelation['Target']

    class Meta:
        table = "story"
        unique_together = (("user_id", "title"),)


class Chapter(Model, TimestampMixin):
    # Primary fields
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story: fields.ForeignKeyRelation['Story'] = fields.ForeignKeyField(
        'models.Story', related_name='chapters', on_delete=fields.CASCADE, index=True
    )
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='chapters', on_delete=fields.CASCADE, index=True
    )
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    published = fields.BooleanField(default=False)

    # Word count tracking
    word_count = fields.IntField(default=0)
    last_extracted_word_count = fields.IntField(null=True)

    # Condensed context (rolling context extraction result)
    condensed_context = fields.TextField(null=True)
    timeline_context = fields.TextField(null=True)
    emotional_arc = fields.TextField(null=True)

    # Extraction metadata
    last_extracted_at = fields.DatetimeField(null=True)
    extraction_version = fields.CharField(max_length=50, null=True)

    # Linked list for chapter ordering (self-referencing)
    next_chapter: fields.ForeignKeyRelation['Chapter'] = fields.ForeignKeyField(
        'models.Chapter', related_name='prev_of', null=True, on_delete=fields.SET_NULL
    )
    prev_chapter: fields.ForeignKeyRelation['Chapter'] = fields.ForeignKeyField(
        'models.Chapter', related_name='next_of', null=True, on_delete=fields.SET_NULL
    )

    class Meta:
        table = "chapter"
        unique_together = (("user_id", "story_id", "title"),)

    @staticmethod
    def get_chapter_number(chapter_id: str, path_array: Optional[List[str]]) -> int:
        """Get chapter number from a story's path_array without traversing relationships."""
        if not path_array:
            return 1
        try:
            return path_array.index(chapter_id) + 1
        except ValueError as e:
            raise ValueError(
                f"Chapter {chapter_id} not found in path_array. "
                f"Expected one of: {path_array}"
            ) from e

    @property
    def has_extractions(self) -> bool:
        """Check if extraction is complete (condensed context exists)"""
        return bool(self.condensed_context)


class Target(Model, TimestampMixin):
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story: fields.ForeignKeyRelation['Story'] = fields.ForeignKeyField(
        'models.Story', related_name='target', on_delete=fields.CASCADE, index=True
    )
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='targets', on_delete=fields.CASCADE, index=True
    )
    quota = fields.IntField(default=0)
    frequency = fields.CharEnumField(FrequencyType, default=FrequencyType.DAILY)
    from_date = fields.DatetimeField(default=datetime.utcnow)
    to_date = fields.DatetimeField(default=datetime.utcnow)

    class Meta:
        table = "target"
        unique_together = (("story_id", "frequency"),)



