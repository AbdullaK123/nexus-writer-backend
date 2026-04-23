from typing import Optional
from pydantic import ValidationError
from src.data.models import Summary, Chapter, Story, Extraction
from src.data.schemas.extraction import VoiceProfile
from src.infrastructure.ai.enums import JobType, SummaryType
from src.service.exceptions import NotFoundError
from src.service.utils.decorators import handle_service_errors
from tortoise.query_utils import Prefetch
from textwrap import dedent
import asyncio
from loguru import logger

from src.shared.utils.html import html_to_plain_text


def _format_voice_profile(data: dict) -> Optional[str]:

    try:
        profile = VoiceProfile(**data)
    except ValidationError as e:
        logger.warning("context.voice_profile.invalid", error=str(e))
        return None

    lines = ["===== VOICE PROFILE =====", ""]

    lines.append(f"Rhythm: {profile.rhythm}")
    lines.append("")

    if profile.signature_features:
        lines.append("Signature features:")
        lines.extend(f"  - {feat}" for feat in profile.signature_features)
        lines.append("")

    lines.append("Per-chapter pacing and tone:")
    for i, (pace, tones) in enumerate(zip(profile.pacing, profile.tone), start=1):
        tone_str = ", ".join(tones) if tones else "—"
        lines.append(f"  Chapter {i}: {pace.value} | {tone_str}")

    return "\n".join(lines)



@handle_service_errors
async def get_context_by_type(
    summary_type: SummaryType, 
    story_id: str,
    chapter_id: Optional[str] = None
) -> str:

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

    path = story_with_summaries.path_array

    if chapter_id and chapter_id not in path:
        raise NotFoundError("Chapter not found in story")

    prefix = path[: path.index(chapter_id) + 1] if chapter_id else path

    position = {cid: i for i, cid in enumerate(prefix)}

    summaries = sorted(
        (s for s in story_with_summaries.summaries if str(s.chapter_id) in position),
        key=lambda s: position[str(s.chapter_id)],
    )

    chunks = [
        dedent(f"""
            ===== Chapter {position[str(s.chapter_id)] + 1} {summary_type.value.upper()} SUMMARY =====
            {s.content}
        """).strip()
        for s in summaries
    ]

    return "\n\n".join(chunks)




@handle_service_errors
async def get_story_context(story_id: str, chapter_id: Optional[str] = None) -> str:
    logger.info("context.get_story_context.start", story_id=story_id)
    
    summary_types = [
        SummaryType.CHARACTER,
        SummaryType.PLOT,
        SummaryType.STYLE,
        SummaryType.WORLD,
    ]

    results = await asyncio.gather(
        *(
            get_context_by_type(summary_type, story_id, chapter_id)
            for summary_type in summary_types
        ),
        return_exceptions=True,
    )

    chunks = []

    for summary_type, result in zip(summary_types, results):
        if isinstance(result, Exception):
            logger.warning(
                "ai.get_story_context.failed_full_context_retrieval",
                type=summary_type,
                error=str(result),
            )
            continue

        if not result:
            continue

        chunks.append(
            dedent(f"""\
                {result}
            """).strip()
        )

    logger.info("context.get_story_context.done", story_id=story_id, chunk_count=len(chunks))
    return "\n\n".join(chunks)


@handle_service_errors
async def get_editor_context(story_id: str, chapter_id: str) -> str:

    story = await (
        Story
            .get_or_none(id=story_id)
            .prefetch_related(
                Prefetch("chapters", queryset=Chapter.filter(id=chapter_id))
            )
    )

    if story is None:
        raise NotFoundError("Story not found")
    if not story.path_array or chapter_id not in story.path_array:
        raise NotFoundError("Chapter does not exist in story")

    chapter = next(iter(story.chapters), None)
    if chapter is None:
        raise NotFoundError("Chapter not found")

    chapter_number = story.path_array.index(chapter_id) + 1

    story_context, voice_profile = await asyncio.gather(
        get_story_context(story_id, chapter_id),
        Extraction.filter(story_id=story_id, type=JobType.VOICE).first(),
    )

    sections = []

    if story_context:
        sections.append(story_context)

    if voice_profile:
        formatted = _format_voice_profile(voice_profile.data)
        if formatted:
            sections.append(formatted)

    sections.append(dedent(f"""\
        ===== CHAPTER UNDER REVIEW: Chapter {chapter_number} — {chapter.title} =====
        {html_to_plain_text(chapter.content)}
    """).strip())

    return "\n\n".join(sections)

