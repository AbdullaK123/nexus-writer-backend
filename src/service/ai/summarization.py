from typing import List, Optional

from src.infrastructure.ai import AIProvider, prompts
from src.infrastructure.config import config
from src.data.models import Summary, Chapter, SummaryType
from src.shared.utils.html import html_to_plain_text
from src.service.exceptions import NotFoundError
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE, set_user_id
import asyncio
from tortoise import Tortoise


log = get_layer_logger(LAYER_SERVICE)

PROMPT_MAP = {
    SummaryType.CHARACTER: prompts.CHARACTER_SUMMARY_PROMPT,
    SummaryType.PLOT: prompts.PLOT_SUMMARY_PROMPT,
    SummaryType.STYLE: prompts.STYLE_SUMMARY_PROMPT,
    SummaryType.WORLD: prompts.WORLD_SUMMARY_PROMPT
}

MAX_TOKENS_MAP = {
    SummaryType.CHARACTER: config.ai.max_tokens.character,
    SummaryType.PLOT: config.ai.max_tokens.plot,
    SummaryType.STYLE: config.ai.max_tokens.style,
    SummaryType.WORLD: config.ai.max_tokens.world
}


async def _fetch_chapter_content(chapter_id: str) -> Chapter:
    chapter = await (
        Chapter
            .filter(id=chapter_id)
            .only("content", "id", "story")
            .first()
    )

    if chapter is None:
        raise NotFoundError("Chapter not found")
    return chapter


async def _get_subsequent_chapter_ids(story_id: str, starting_chapter_id: str) -> List[str]:
    conn = Tortoise.get_connection("default")
    rows = await conn.execute_query_dict(
        """
        SELECT path_array[array_position(path_array, $1) : array_length(path_array, 1)] AS chapter_ids
        FROM story
        WHERE id = $2
        """,
        [starting_chapter_id, story_id]
    )
    if not rows:
        return []
    return rows[0]["chapter_ids"] or []


async def _generate_summary(
    provider: AIProvider, 
    type: SummaryType,
    chapter: Chapter
) -> None:

    summary_text = await provider.generate(
        system_prompt=PROMPT_MAP[type],
        text=html_to_plain_text(chapter.content),
        max_tokens=MAX_TOKENS_MAP[type]
    )

    await Summary.update_or_create(
        defaults={"content": summary_text},
        story_id=chapter.story_id,  # type: ignore[attr-defined]
        chapter_id=chapter.id,
        type=type,
    )


async def generate_all_summaries(provider: AIProvider, chapter_id: str) -> None:

    chapter = await _fetch_chapter_content(chapter_id)

    types = [SummaryType.CHARACTER, SummaryType.PLOT, SummaryType.STYLE, SummaryType.WORLD]

    results = await asyncio.gather(
        *(_generate_summary(provider, t, chapter) for t in types),
        return_exceptions=True
    )

    for type, result in zip(types, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.generate_summaries.summary_task_failed",
                type=type,
                error=str(result)
            )


async def regenerate_stale_summaries(
    provider: AIProvider, 
    batch_size: int = config.ai.regeneration_batch_size
) -> None:

    stale_chapter_ids = await (
        Summary
            .filter(is_stale=True)
            .distinct()
            .limit(batch_size)
            .values_list("chapter_id", flat=True)
    )

    if not stale_chapter_ids:
        return

    results = await asyncio.gather(
        *(generate_all_summaries(provider, cid) for cid in stale_chapter_ids), #type: ignore
        return_exceptions=True
    )

    for chapter_id, result in zip(stale_chapter_ids, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.regenerate_stale_summaries.regeneration_failed",
                chapter_id=chapter_id,
                error=str(result)
            )


async def mark_summaries_stale(story_id: str, starting_chapter_id: str) -> None:

    cids_now_stale = await _get_subsequent_chapter_ids(story_id, starting_chapter_id)

    if not cids_now_stale:
        return
    
    await Summary.filter(chapter_id__in=cids_now_stale).update(is_stale=True)
