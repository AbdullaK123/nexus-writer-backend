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
