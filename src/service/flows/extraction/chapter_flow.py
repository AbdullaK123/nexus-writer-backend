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
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.infrastructure.config import settings
from src.data.models import Chapter
from src.data.models.ai.character import CharacterExtraction
from src.data.models.ai.plot import PlotExtraction
from src.data.models.ai.world import WorldExtraction
from src.data.models.ai.structure import StructureExtraction
from src.data.models.ai.context import CondensedChapterContext
from src.data.schemas.jobs import (
    JobType,
    ExtractionEventData,
    ChapterStartedData,
    ExtractionCompleteData,
)
from src.service.flows.publisher import FlowPublisher, create_flow_pubsub
from src.service.flows.extraction.tasks import (
    extract_characters_task,
    extract_plot_task,
    extract_world_task,
    extract_structure_task,
    synthesize_context_task,
    save_chapter_extraction_task,
)
from src.infrastructure.config.prefect import CHAPTER_FLOW_TIMEOUT


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
        events = [e.event for e in plot_result.events[:5]]
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
    max_wait: int = 600,
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
                log.info(
                    "extraction.predecessors_complete",
                    chapter_number=chapter_number,
                    waited_seconds=elapsed,
                )
            return

        log.info(
            "extraction.waiting_for_predecessors",
            chapter_number=chapter_number,
            blocking_count=len(blocking),
            elapsed_seconds=elapsed,
            max_wait_seconds=max_wait,
        )
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    log.warning(
        "extraction.predecessors_timeout: proceeding without predecessors",
        chapter_number=chapter_number,
        max_wait_seconds=max_wait,
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

    previous_chapters_list = await Chapter.filter(id__in=previous_chapter_ids)
    previous_chapters = {ch.id: ch for ch in previous_chapters_list}

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
    content: str,
    user_id: str = "",
    use_lfm: bool = False,
) -> ChapterExtractionResult:
    """Extract context from a single chapter with checkpointing.
    
    Individual extraction failures are tolerated — fallback empty models
    are substituted so the flow always produces a usable result.
    """
    pubsub = create_flow_pubsub(settings.redis_url, ExtractionEventData)  # type: ignore
    pub = FlowPublisher[ExtractionEventData](
        pubsub=pubsub,
        user_id=user_id,
        story_id=story_id,
        job_type=JobType.EXTRACTION,
        total_steps=5,
    )
    await pub.flow_started(data=ChapterStartedData(chapter_id=chapter_id, chapter_number=chapter_number))
    
    # 1. Wait for predecessor chapters to finish extracting
    await pub.task_started("predecessor_wait", message="Waiting for predecessor extractions")
    await _wait_for_predecessor_extractions(story_id, chapter_number, story_path_array)
    await pub.task_complete("predecessor_wait")

    # 2. Build accumulated context from predecessor results (after they're done)
    await pub.task_started("build_context", message="Building accumulated context")
    accumulated_context = await _build_accumulated_context(chapter_number, story_path_array)
    await pub.task_complete("build_context")

    log.info("extraction.started", chapter_number=chapter_number, chapter_id=chapter_id)

    failed_extractions: List[str] = []

    # Run all 4 extractions concurrently — gather instead of TaskGroup
    # so that one failure doesn't cancel the others
    await pub.task_started("run_extractions", message="Running AI extractions")
    results = await asyncio.gather(
        extract_characters_task(accumulated_context, content, chapter_number, chapter_title, use_lfm=use_lfm, story_id=story_id),
        extract_plot_task(accumulated_context, content, chapter_number, chapter_title, use_lfm=use_lfm, story_id=story_id),
        extract_world_task(accumulated_context, content, chapter_number, chapter_title, use_lfm=use_lfm, story_id=story_id),
        extract_structure_task(accumulated_context, content, chapter_number, chapter_title, use_lfm=use_lfm, story_id=story_id),
        return_exceptions=True,
    )

    # Unpack results — substitute fallbacks for any failures
    if isinstance(results[0], BaseException):
        log.error("extraction.characters_failed", chapter_number=chapter_number, error=str(results[0]))
        failed_extractions.append("characters")
        character_result = CharacterExtraction.empty()
    else:
        character_result = results[0]

    if isinstance(results[1], BaseException):
        log.error("extraction.plot_failed", chapter_number=chapter_number, error=str(results[1]))
        failed_extractions.append("plot")
        plot_result = PlotExtraction.empty()
    else:
        plot_result = results[1]

    if isinstance(results[2], BaseException):
        log.error("extraction.world_failed", chapter_number=chapter_number, error=str(results[2]))
        failed_extractions.append("world")
        world_result = WorldExtraction.empty()
    else:
        world_result = results[2]

    if isinstance(results[3], BaseException):
        log.error("extraction.structure_failed", chapter_number=chapter_number, error=str(results[3]))
        failed_extractions.append("structure")
        structure_result = StructureExtraction.empty()
    else:
        structure_result = results[3]
    
    if failed_extractions:
        log.warning(
            "extraction.partial: some extractions failed, using fallbacks",
            chapter_number=chapter_number,
            failed_count=len(failed_extractions),
            failed=failed_extractions,
        )
        await pub.task_complete("run_extractions", message=f"Partial: {', '.join(failed_extractions)} failed")
    else:
        log.info("extraction.all_complete: synthesizing", chapter_number=chapter_number)
        await pub.task_complete("run_extractions")
    
    # Synthesize into condensed context — with fallback
    await pub.task_started("synthesize", message="Synthesizing context")
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
            use_lfm=use_lfm,
        )
        await pub.task_complete("synthesize")
    except Exception as e:
        log.error("extraction.synthesis_failed: building fallback context", chapter_number=chapter_number, error=str(e))
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
        await pub.task_complete("synthesize", message="Used fallback context")
    
    # CHECKPOINT: Always save — even partial results are better than nothing
    await pub.task_started("save", message="Saving extraction results")
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
    await pub.task_complete("save")
    
    is_partial = len(failed_extractions) > 0
    if is_partial:
        log.warning(
            "extraction.saved_partial",
            chapter_number=chapter_number,
            chapter_id=chapter_id,
            failed=failed_extractions,
        )
    else:
        log.info("extraction.saved", chapter_number=chapter_number, chapter_id=chapter_id)
    
    await pub.flow_complete(data=ExtractionCompleteData(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        is_partial=is_partial,
        failed_extractions=failed_extractions,
    ))

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