# mypy: disable-error-code="var-annotated"
from tortoise import fields
from tortoise.models import Model
from typing import Optional, List
from src.data.models.enums import generate_uuid
from src.data.models.user import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.models import Story, User, Extraction


class Chapter(Model, TimestampMixin):
    # Primary fields
    id = fields.CharField(max_length=36, pk=True, default=generate_uuid)
    story: fields.ForeignKeyRelation["Story"] = fields.ForeignKeyField(
        "models.Story", related_name="chapters", on_delete=fields.CASCADE, index=True
    )
    story_id: str
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="chapters", on_delete=fields.CASCADE, index=True
    )
    user_id: str
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    published = fields.BooleanField(default=False)

    # Word count tracking
    word_count = fields.IntField(default=0)

    # Linked list for chapter ordering (self-referencing)
    next_chapter: fields.ForeignKeyNullableRelation["Chapter"] = fields.ForeignKeyField(
        "models.Chapter",
        related_name="prev_of",
        null=True,
        on_delete=fields.SET_NULL,
    )
    next_chapter_id: Optional[str]
    prev_chapter: fields.ForeignKeyNullableRelation["Chapter"] = fields.ForeignKeyField(
        "models.Chapter",
        related_name="next_of",
        null=True,
        on_delete=fields.SET_NULL,
    )
    prev_chapter_id: Optional[str]

    extractions: fields.ReverseRelation["Extraction"]

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
