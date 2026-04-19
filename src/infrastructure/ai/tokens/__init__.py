from src.infrastructure.ai.prompts import SummaryType
from src.infrastructure.config import config
from src.infrastructure.ai.enums import ExtractionType


MAX_TOKENS_MAP = {
    SummaryType.CHARACTER: config.ai.max_tokens.summary.character,
    SummaryType.PLOT: config.ai.max_tokens.summary.plot,
    SummaryType.STYLE: config.ai.max_tokens.summary.style,
    SummaryType.WORLD: config.ai.max_tokens.summary.world,
    ExtractionType.PLOT_THREAD: config.ai.max_tokens.extraction.plot_threads,
    ExtractionType.CHARACTER: config.ai.max_tokens.extraction.character,
    ExtractionType.WORLD_BIBLE: config.ai.max_tokens.extraction.world_bible,
    ExtractionType.VOICE: config.ai.max_tokens.extraction.voice
}