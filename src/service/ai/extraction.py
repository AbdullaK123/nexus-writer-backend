from src.data.models.enums import ExtractionType
from src.data.models.story import Story
from src.infrastructure.ai.tokens import MAX_TOKENS_MAP
from src.infrastructure.ai.prompts import PROMPT_MAP
from src.infrastructure.ai.enums import SummaryType
from src.infrastructure.ai import AIProvider
from src.data.models import Summary, Chapter, Extraction
from src.service.ai.utils import fetch_chapter_content, get_subsequent_chapter_ids
from src.shared.utils.html import html_to_plain_text
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
import src.service.ai.context as ctx
from src.data.schemas.extraction import CharacterRoster, PlotThreadLedger, VoiceProfile, WorldBible
import asyncio
from typing import Any


log = get_layer_logger(LAYER_SERVICE)

SCHEMA_MAP = {
    ExtractionType.CHARACTER: CharacterRoster,
    ExtractionType.WORLD_BIBLE: WorldBible,
    ExtractionType.VOICE: VoiceProfile,
    ExtractionType.PLOT_THREAD: PlotThreadLedger
}

EXTRACTION_TO_SUMMARY_MAP = {
    ExtractionType.CHARACTER: SummaryType.CHARACTER,
    ExtractionType.WORLD_BIBLE: SummaryType.WORLD,
    ExtractionType.VOICE: SummaryType.STYLE,
    ExtractionType.PLOT_THREAD: SummaryType.PLOT
}


async def generate_extraction_by_type(
    provider: AIProvider, 
    extraction_type: ExtractionType, 
    story_id: str 
) -> None:
    context = await ctx.get_context_by_type(
        EXTRACTION_TO_SUMMARY_MAP[extraction_type],
        story_id
    )    
    extraction: Any  =  await provider.extract(  # type: ignore[arg-type]
        system_prompt=PROMPT_MAP[extraction_type],
        text=context,
        max_tokens=MAX_TOKENS_MAP[extraction_type],
        schema=SCHEMA_MAP[extraction_type]
    )
    await Extraction.update_or_create(
        defaults={"data": extraction.model_dump()},
        story_id=story_id,  # type: ignore[attr-defined]
        type=extraction_type,
    )
    log.info("extraction.generate.done", story_id=story_id, type=extraction_type)


async def generate_all_extractions(provider: AIProvider, story_id: str) -> None:

    extraction_types = [
        ExtractionType.CHARACTER,
        ExtractionType.WORLD_BIBLE,
        ExtractionType.VOICE,
        ExtractionType.PLOT_THREAD
    ]

    results = await asyncio.gather(
        *(generate_extraction_by_type(provider, t, story_id) for t in extraction_types),
        return_exceptions=True,
    )

    for extraction_type, result in zip(extraction_types, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.generate_extraction.extraction_task_failed",
                type=extraction_type,
                error=str(result),
            )


async def mark_extractions_stale(story_id: str) -> None:
    await Extraction.filter(story_id=story_id).update(is_stale=True)
    log.info("extraction.mark_stale.done", story_id=story_id)
