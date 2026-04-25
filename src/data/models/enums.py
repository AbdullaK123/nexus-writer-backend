import uuid
from enum import StrEnum


def generate_uuid():
    return str(uuid.uuid4())


class StoryStatus(StrEnum):
    COMPLETE = "Complete"
    ON_HIATUS = "On Hiatus"
    ONGOING = "Ongoing"
