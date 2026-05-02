"""Domain enums + id generator. Lives in `schemas` (not `models`) because
the Tortoise model layer is gone — these are pure-Python values shared
between the schema, repository, and service layers."""
from enum import StrEnum

from uuid_extensions import uuid7


def generate_uuid() -> str:
    return str(uuid7())


class StoryStatus(StrEnum):
    COMPLETE = "Complete"
    ON_HIATUS = "On Hiatus"
    ONGOING = "Ongoing"
