"""
Tier 2: Single chapter extraction sub-flow with checkpointing.

This flow:
- Runs all 4 AI extractions concurrently
- Tolerates individual extraction failures (uses fallback empty models)
- Synthesizes results (with fallback if synthesis fails)
- Always commits to database — never leaves the chapter in a broken state
- Returns results for rolling context
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List
from prefect import flow
from prefect.runtime import flow_run
from loguru import logger
from app.config.settings import app_config
from app.core.mongodb import MongoDB
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
from app.config.prefect import DEFAULT_FLOW_RETRIES, CHAPTER_FLOW_TIMEOUT


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
    
    if world_result.locations:
        locs = [loc.name for loc in world_result.locations]
        parts.append(f"Locations: {', '.join(locs)}")
    
    if world_result.timeline:
        markers = [f"{t.event} ({t.time_reference})" for t in world_result.timeline[:5]]
        parts.append(f"Timeline: {'; '.join(markers)}")
    
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


@flow(
    name="extract-single-chapter",
    retries=DEFAULT_FLOW_RETRIES,
    retry_delay_seconds=60,
    timeout_seconds=CHAPTER_FLOW_TIMEOUT,
    persist_result=True,
)
async def extract_single_chapter_flow(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    accumulated_context: str,
    content: str
) -> ChapterExtractionResult:
    """Extract context from a single chapter with checkpointing.
    
    Individual extraction failures are tolerated — fallback empty models
    are substituted so the flow always produces a usable result.
    """
    
    await MongoDB.connect(app_config.mongodb_url)

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