from src.data.models import Summary, Story
from src.infrastructure.ai.enums import SummaryType
from src.service.exceptions import NotFoundError
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
from tortoise.query_utils import Prefetch
from textwrap import dedent
import asyncio

log = get_layer_logger(LAYER_SERVICE)


async def get_context_by_type(summary_type: SummaryType, story_id: str) -> str:

    story_with_summaries = await (
        Story.filter(id=story_id)
        .only("id", "path_array")
        .prefetch_related(
            Prefetch("summaries", queryset=Summary.filter(type=summary_type))
        )
        .first()
    )

    if story_with_summaries is None:
        raise NotFoundError("Story not found")

    if not story_with_summaries.path_array:
        return ""

    position = {cid: i for i, cid in enumerate(story_with_summaries.path_array)}
    summaries = sorted(
        story_with_summaries.summaries,
        key=lambda s: position.get(str(s.chapter_id), len(position)),  # type: ignore
    )

    chunks = [
        dedent(f"""\
            ===== Chapter {i + 1} =====
            {s.content}
        """).strip()
        for i, s in enumerate(summaries)
    ]

    return "\n\n".join(chunks)


async def get_story_context(story_id: str) -> str:
    log.info("context.get_story_context.start", story_id=story_id)
    
    summary_types = [
        SummaryType.CHARACTER,
        SummaryType.PLOT,
        SummaryType.STYLE,
        SummaryType.WORLD,
    ]

    results = await asyncio.gather(
        *(
            get_context_by_type(summary_type, story_id)
            for summary_type in summary_types
        ),
        return_exceptions=True,
    )

    chunks = []

    for summary_type, result in zip(summary_types, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.get_story_context.failed_full_context_retrieval",
                type=summary_type,
                error=str(result),
            )
            continue

        if not result:
            continue

        chunks.append(
            dedent(f"""\
                ===== {summary_type.value.upper()} CONTEXT =====
                {result}
            """).strip()
        )

    log.info("context.get_story_context.done", story_id=story_id, chunk_count=len(chunks))
    return "\n\n".join(chunks)
