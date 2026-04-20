from .summarization import *
from .extraction import *
from src.infrastructure.ai.enums import SummaryType, ExtractionType


PROMPT_MAP = {
    SummaryType.CHARACTER: CHARACTER_SUMMARY_PROMPT,
    SummaryType.PLOT: PLOT_SUMMARY_PROMPT,
    SummaryType.STYLE: STYLE_SUMMARY_PROMPT,
    SummaryType.WORLD: WORLD_SUMMARY_PROMPT,
    ExtractionType.WORLD_BIBLE: WORLD_BIBLE_EXTRACTION_PROMPT,
    ExtractionType.CHARACTER: CHARACTER_ROSTER_EXTRACTION_PROMPT,
    ExtractionType.VOICE: VOICE_PROFILE_EXTRACTION_PROMPT,
    ExtractionType.PLOT_THREAD: PLOT_THREADS_EXTRACTION_PROMPT,
}
