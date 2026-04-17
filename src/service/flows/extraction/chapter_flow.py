"""
Tier 2: Single chapter extraction with checkpointing.

This module:
- Waits for predecessor chapters to finish extracting (ordering guard via JobRegistry)
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

from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.infrastructure.config import settings, config
from src.infrastructure.redis.job_registry import JobRegistry, RegistryStatus
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
from src.service.flows.publisher import FlowPublisher
from src.service.flows.extraction.tasks import (
    extract_characters_task,
    extract_plot_task,
    extract_world_task,
    extract_structure_task,
    synthesize_context_task,
    save_chapter_extraction_task,
)


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
    registry: JobRegistry,
    story_id: str,
    chapter_number: int,
    story_path_array: List[str],
    poll_interval: int = config.worker.predecessor_poll_interval,
    max_wait: int = config.worker.predecessor_max_wait,
) -> None:
    """Poll until all predecessor chapter extractions finish.

    Uses JobRegistry tag-based filtering instead of Prefect API.
    """
    if chapter_number <= 1:
        return

    predecessor_ids = set(story_path_array[:chapter_number - 1])
    if not predecessor_ids:
        return

    elapsed = 0
    while elapsed < max_wait:
        active_jobs = await registry.find_by_tags(
            ["extraction", f"story:{story_id}"],
            statuses=[RegistryStatus.QUEUED, RegistryStatus.RUNNING],
        )

        blocking: List[str] = []
        for job_id in active_jobs:
            tags = await registry.get_tags(job_id)
            for tag in tags:
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


async def _run_extraction(
    registry: JobRegistry,
    job_run_id: str,
    *,
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    story_id: str,
    story_path_array: List[str],
    content: str,
    user_id: str = "",
) -> ChapterExtractionResult:
    """Core extraction logic, callable from both the arq job and reextraction."""
    pub = FlowPublisher[ExtractionEventData](
        redis_url=settings.redis_url,
        user_id=user_id,
        story_id=story_id,
        job_type=JobType.EXTRACTION,
        total_steps=5,
        job_run_id=job_run_id,
    )
    try:
        await pub.flow_started(data=ChapterStartedData(chapter_id=chapter_id, chapter_number=chapter_number))
    
        # 1. Wait for predecessor chapters to finish extracting
        await pub.task_started("predecessor_wait", message="Waiting for predecessor extractions")
        await _wait_for_predecessor_extractions(registry, story_id, chapter_number, story_path_array)
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
            extract_characters_task(accumulated_context, content, chapter_number, chapter_title, story_id=story_id),
            extract_plot_task(accumulated_context, content, chapter_number, chapter_title, story_id=story_id),
            extract_world_task(accumulated_context, content, chapter_number, chapter_title, story_id=story_id),
            extract_structure_task(accumulated_context, content, chapter_number, chapter_title, story_id=story_id),
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
    finally:
        await pub.close()


async def extract_single_chapter(ctx: dict, **kwargs) -> ChapterExtractionResult:
    """arq job entry point — wraps _run_extraction with registry status tracking."""
    registry: JobRegistry = ctx["registry"]
    job_id: str = ctx["job_id"]
    await registry.set_status(job_id, RegistryStatus.RUNNING)
    try:
        result = await _run_extraction(registry, job_id, **kwargs)
        await registry.set_status(job_id, RegistryStatus.COMPLETE)
        return result
    except Exception:
        await registry.set_status(job_id, RegistryStatus.FAILED)
        raise