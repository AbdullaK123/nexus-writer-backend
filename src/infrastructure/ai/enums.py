from enum import StrEnum


class SummaryType(StrEnum):
    CHARACTER = "character"
    PLOT = "plot"
    WORLD = "world"
    STYLE = "style"


class JobType(StrEnum):
    PLOT_THREAD = "plot_thread"
    CHARACTER = "character"
    WORLD_BIBLE = "world_bible"
    VOICE = "voice"