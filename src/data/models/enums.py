import uuid
from enum import StrEnum


def generate_uuid():
    return str(uuid.uuid4())


class StoryStatus(StrEnum):
    COMPLETE = "Complete"
    ON_HAITUS = "On Hiatus"
    ONGOING = "Ongoing"


class FrequencyType(StrEnum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"

class SummaryType(StrEnum):
    CHARACTER = "character"
    PLOT = "plot"
    WORLD = "world"
    STYLE = "style"