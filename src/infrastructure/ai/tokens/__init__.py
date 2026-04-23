from src.infrastructure.ai.prompts import SummaryType
from src.infrastructure.config import config
from src.infrastructure.ai.enums import JobType


MAX_TOKENS_MAP = {
    SummaryType.CHARACTER: config.ai.max_tokens.summary.character,
    SummaryType.PLOT: config.ai.max_tokens.summary.plot,
    SummaryType.STYLE: config.ai.max_tokens.summary.style,
    SummaryType.WORLD: config.ai.max_tokens.summary.world,
    JobType.PLOT_THREAD: config.ai.max_tokens.extraction.plot_threads,
    JobType.CHARACTER: config.ai.max_tokens.extraction.character,
    JobType.WORLD_BIBLE: config.ai.max_tokens.extraction.world_bible,
    JobType.VOICE: config.ai.max_tokens.extraction.voice,
    JobType.EDITOR: config.ai.max_tokens.editor,
}
