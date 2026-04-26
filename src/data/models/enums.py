from uuid_extensions import uuid7
from enum import StrEnum


def generate_uuid():
    return str(uuid7())


class StoryStatus(StrEnum):
    COMPLETE = "Complete"
    ON_HIATUS = "On Hiatus"
    ONGOING = "Ongoing"


# in case we want more types of chapter level extractions
class ExtractionType(StrEnum):
    SCENES = "scenes"
