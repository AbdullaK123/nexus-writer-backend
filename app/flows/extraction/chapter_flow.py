"""
Tier 2: Single chapter extraction sub-flow with checkpointing.

This flow:
- Waits for predecessor chapters to finish extracting (ordering guard)
- Builds accumulated context from predecessor results
- Runs all 4 AI extractions concurrently
- Tolerates individual extraction failures (uses fallback empty models)
- Synthesizes results (with fallback if synthesis fails)
- Always commits to database — never leaves the chapter in a broken state
- Returns results for rolling context
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List
from prefect import flow, get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterTags,
    FlowRunFilterState,
    FlowRunFilterStateType,
)
from prefect.client.schemas.objects import StateType
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config.settings import app_config
from app.core.database import engine
from app.core.mongodb import MongoDB
from app.models import Chapter
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.world import WorldExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.context import CondensedChapterContext
from app.flows.extraction.tasks import (
    extract_characters_task,
    extract_plot_task,
    extract_world_task,
    extract_structure_task,
    synthesize_context_task,
    save_chapter_extraction_task,
)
from app.config.prefect import CHAPTER_FLOW_TIMEOUT


@dataclass
class ChapterExtractionResult:
    """Result from single chapter extraction"""
    chapter_id: str
    chapter_number: int
    success: bool
    condensed_context: Optional[str] = None
    character_extraction: Optional[dict] = None
    plot_extraction: Optional[dict] = None
    world_extraction: Optional[dict] = None
    structure_extraction: Optional[dict] = None
    error: Optional[str] = None
    failed_extractions: List[str] = field(default_factory=list)
    is_partial: bool = False


def _build_fallback_context(
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    character_result: CharacterExtraction,
    plot_result: PlotExtraction,
    world_result: WorldExtraction,
) -> CondensedChapterContext:
    """Build a minimal condensed context from whatever extractions we have.
    Used when the AI synthesis task itself fails."""
    
    # Build a best-effort condensed text from raw extraction data
    parts = []
    
    title_text = f" — {chapter_title}" if chapter_title else ""
    parts.append(f"Chapter {chapter_number}{title_text}")
    
    if character_result.characters:
        names = [c.name for c in character_result.characters]
        parts.append(f"Characters: {', '.join(names)}")
    
    if plot_result.events:
        events = [e.description for e in plot_result.events[:5]]
        parts.append(f"Events: {'; '.join(events)}")
    
    if world_result.facts:
        facts = [f"{f.entity}/{f.attribute}/{f.value}" for f in world_result.facts[:5]]
        parts.append(f"Facts: {'; '.join(facts)}")
    
    condensed = "\n".join(parts) if parts else f"Chapter {chapter_number} (extraction incomplete)"
    
    return CondensedChapterContext(
        chapter_id="",  # Will be set by caller
        timeline_context="Unknown — synthesis failed",
        entities_summary=condensed,
        events_summary=condensed,
        character_developments="Unavailable — synthesis failed",
        plot_progression="Unavailable — synthesis failed",
        worldbuilding_additions="Unavailable — synthesis failed",
        themes_present=[],
        emotional_arc="Unknown",
        word_count=word_count,
        estimated_reading_time_minutes=max(1, word_count // 250),
        condensed_text=condensed,
    )


async def _wait_for_predecessor_extractions(
    story_id: str,
    chapter_number: int,
    story_path_array: List[str],
    poll_interval: int = 5,
    max_wait: int = 300,
) -> None:
    """Poll until all predecessor chapter extractions finish.
    
    This runs INSIDE the flow (not in the API server), so all sibling
    flow runs are already registered in Prefect and visible.
    """
    if chapter_number <= 1:
        return

    predecessor_ids = set(story_path_array[:chapter_number - 1])
    if not predecessor_ids:
        return

    elapsed = 0
    while elapsed < max_wait:
        async with get_client() as client:
            flow_runs = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(
                    tags=FlowRunFilterTags(all_=["extraction", f"story:{story_id}"]),
                    state=FlowRunFilterState(
                        type=FlowRunFilterStateType(any_=[
                            StateType.RUNNING,
                            StateType.PENDING,
                            StateType.SCHEDULED,
                        ])
                    )
                )
            )

        blocking: List[str] = []
        for fr in flow_runs:
            for tag in fr.tags:
                if tag.startswith("chapter:"):
                    ch_id = tag.split(":", 1)[1]
                    if ch_id in predecessor_ids:
                        blocking.append(ch_id)

        if not blocking:
            if elapsed > 0:
                logger.info(f"Chapter {chapter_number}: predecessors complete after {elapsed}s wait")
            return

        logger.info(
            f"Chapter {chapter_number}: waiting for {len(blocking)} predecessor(s) "
            f"({elapsed}s / {max_wait}s)"
        )
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    logger.warning(
        f"Chapter {chapter_number}: predecessors still running after {max_wait}s, proceeding anyway"
    )


async def _build_accumulated_context(
    chapter_number: int,
    story_path_array: List[str],
) -> str:
    """Build accumulated context from predecessor chapters' condensed contexts (Postgres)."""
    if chapter_number <= 1:
        return ""

    previous_chapter_ids = story_path_array[:chapter_number - 1]
    if not previous_chapter_ids:
        return ""

    async with AsyncSession(engine) as db:
        query = select(Chapter).where(Chapter.id.in_(previous_chapter_ids))  # type: ignore[union-attr]
        result = await db.execute(query)
        previous_chapters = {ch.id: ch for ch in result.scalars().all()}

    contexts = []
    for i, ch_id in enumerate(previous_chapter_ids):
        ch = previous_chapters.get(ch_id)
        if ch and ch.condensed_context:
            contexts.append(f"=== Chapter {i + 1} ===\n{ch.condensed_context}")

    return "\n\n".join(contexts)


@flow(
    name="extract-single-chapter",
    retries=0,
    timeout_seconds=CHAPTER_FLOW_TIMEOUT,
    persist_result=True,
)
async def extract_single_chapter_flow(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    story_id: str,
    story_path_array: List[str],
    content: str
) -> ChapterExtractionResult:
    """Extract context from a single chapter with checkpointing.
    
    Individual extraction failures are tolerated — fallback empty models
    are substituted so the flow always produces a usable result.
    """
    
    await MongoDB.connect(app_config.mongodb_url)

    # 1. Wait for predecessor chapters to finish extracting
    await _wait_for_predecessor_extractions(story_id, chapter_number, story_path_array)

    # 2. Build accumulated context from predecessor results (after they're done)
    accumulated_context = await _build_accumulated_context(chapter_number, story_path_array)

    logger.info(f"Starting extraction for Chapter {chapter_number} ({chapter_id})")

    failed_extractions: List[str] = []

    # Run all 4 extractions concurrently — gather instead of TaskGroup
    # so that one failure doesn't cancel the others
    results = await asyncio.gather(
        extract_characters_task(accumulated_context, content, chapter_number, chapter_title),
        extract_plot_task(accumulated_context, content, chapter_number, chapter_title),
        extract_world_task(accumulated_context, content, chapter_number, chapter_title),
        extract_structure_task(accumulated_context, content, chapter_number, chapter_title),
        return_exceptions=True,
    )

    # Unpack results — substitute fallbacks for any failures
    if isinstance(results[0], BaseException):
        logger.error(f"Chapter {chapter_number}: Character extraction failed: {results[0]}")
        failed_extractions.append("characters")
        character_result = CharacterExtraction.empty()
    else:
        character_result = results[0]

    if isinstance(results[1], BaseException):
        logger.error(f"Chapter {chapter_number}: Plot extraction failed: {results[1]}")
        failed_extractions.append("plot")
        plot_result = PlotExtraction.empty()
    else:
        plot_result = results[1]

    if isinstance(results[2], BaseException):
        logger.error(f"Chapter {chapter_number}: World extraction failed: {results[2]}")
        failed_extractions.append("world")
        world_result = WorldExtraction.empty()
    else:
        world_result = results[2]

    if isinstance(results[3], BaseException):
        logger.error(f"Chapter {chapter_number}: Structure extraction failed: {results[3]}")
        failed_extractions.append("structure")
        structure_result = StructureExtraction.empty()
    else:
        structure_result = results[3]
    
    if failed_extractions:
        logger.warning(
            f"Chapter {chapter_number}: {len(failed_extractions)}/4 extractions failed "
            f"({', '.join(failed_extractions)}). Using fallbacks."
        )
    else:
        logger.info(f"Chapter {chapter_number}: All extractions complete, synthesizing...")
    
    # Synthesize into condensed context — with fallback
    try:
        synthesis_result = await synthesize_context_task(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            word_count=word_count,
            character_extraction=character_result.model_dump(),
            plot_extraction=plot_result.model_dump(),
            world_extraction=world_result.model_dump(),
            structure_extraction=structure_result.model_dump(),
        )
    except Exception as e:
        logger.error(f"Chapter {chapter_number}: Synthesis failed: {e}. Building fallback context.")
        failed_extractions.append("synthesis")
        synthesis_result = _build_fallback_context(
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            word_count=word_count,
            character_result=character_result,
            plot_result=plot_result,
            world_result=world_result,
        )
        synthesis_result.chapter_id = chapter_id
    
    # CHECKPOINT: Always save — even partial results are better than nothing
    await save_chapter_extraction_task(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        character_extraction=character_result,
        plot_extraction=plot_result,
        world_extraction=world_result,
        structure_extraction=structure_result,
        context_synthesis=synthesis_result,
        word_count=word_count,
    )
    
    is_partial = len(failed_extractions) > 0
    if is_partial:
        logger.warning(
            f"⚠️ Chapter {chapter_number} extraction saved (partial — "
            f"failed: {', '.join(failed_extractions)})"
        )
    else:
        logger.success(f"✅ Chapter {chapter_number} extraction complete and checkpointed")
    
    return ChapterExtractionResult(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        success=True,
        condensed_context=synthesis_result.condensed_text,  
        character_extraction=character_result.model_dump(), 
        plot_extraction=plot_result.model_dump(),
        world_extraction=world_result.model_dump(),
        structure_extraction=structure_result.model_dump(),
        failed_extractions=failed_extractions,
        is_partial=is_partial,
    )