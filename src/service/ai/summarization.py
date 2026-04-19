from typing import List
from src.infrastructure.ai.tokens import MAX_TOKENS_MAP
from src.infrastructure.ai.prompts import PROMPT_MAP
from src.infrastructure.ai.enums import SummaryType
from src.infrastructure.ai import AIProvider
from src.data.models import Summary, Chapter
from src.shared.utils.html import html_to_plain_text
from src.service.exceptions import NotFoundError
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
import asyncio
from tortoise import Tortoise


log = get_layer_logger(LAYER_SERVICE)

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

async def mark_summaries_stale(story_id: str, starting_chapter_id: str) -> None:

    cids_now_stale = await _get_subsequent_chapter_ids(story_id, starting_chapter_id)

    if not cids_now_stale:
        return
    
    await Summary.filter(chapter_id__in=cids_now_stale).update(is_stale=True)
