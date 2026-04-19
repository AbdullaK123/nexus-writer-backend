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

class ExtractionType(StrEnum):
    PLOT_THREAD = "plot_thread"
    CHARACTER = "character"
    WORLD_BIBLE = "world_bible"
    VOICE = "voice"

class JobType(StrEnum):
    PLOT_THREAD = "plot_thread"
    CHARACTER = "character"
    WORLD_BIBLE = "world_bible"
    VOICE = "voice"


class JobStatus(StrEnum):
    QUEUED = "queued"
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"