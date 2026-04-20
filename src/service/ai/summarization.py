from src.infrastructure.ai.tokens import MAX_TOKENS_MAP
from src.infrastructure.ai.prompts import PROMPT_MAP
from src.infrastructure.ai.enums import SummaryType
from src.infrastructure.ai import AIProvider
from src.data.models import Summary, Chapter
from src.service.ai.utils import fetch_chapter_content, get_subsequent_chapter_ids
from src.shared.utils.html import html_to_plain_text
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
import asyncio


log = get_layer_logger(LAYER_SERVICE)


async def generate_summary_by_type(
    provider: AIProvider, 
    summary_type: SummaryType, 
    chapter: Chapter
) -> None:
    
    summary_text = await provider.generate(
        system_prompt=PROMPT_MAP[summary_type],
        text=html_to_plain_text(chapter.content),
        max_tokens=MAX_TOKENS_MAP[summary_type],
    )

    await Summary.update_or_create(
        defaults={"content": summary_text},
        story_id=chapter.story_id,  # type: ignore[attr-defined]
        chapter_id=chapter.id,
        type=summary_type,
    )
    log.info("summary.generate.done", chapter_id=chapter.id, type=summary_type)


async def generate_all_summaries(provider: AIProvider, chapter_id: str) -> None:

    chapter = await fetch_chapter_content(chapter_id)
    log.info("summary.generate_all.start", chapter_id=chapter_id)

    summary_types = [
        SummaryType.CHARACTER,
        SummaryType.PLOT,
        SummaryType.STYLE,
        SummaryType.WORLD,
    ]

    results = await asyncio.gather(
        *(generate_summary_by_type(provider, t, chapter) for t in summary_types),
        return_exceptions=True,
    )

    for summary_type, result in zip(summary_types, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.generate_summaries.summary_task_failed",
                type=summary_type,
                error=str(result),
            )


async def mark_summaries_stale(story_id: str, starting_chapter_id: str) -> None:

    cids_now_stale = await get_subsequent_chapter_ids(story_id, starting_chapter_id)

    if not cids_now_stale:
        return

    await Summary.filter(chapter_id__in=cids_now_stale).update(is_stale=True)
    log.info("summary.mark_stale.done", story_id=story_id, stale_count=len(cids_now_stale))
