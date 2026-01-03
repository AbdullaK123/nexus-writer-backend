"""
Tier 1: Individual AI extraction tasks with circuit breaker protection.

Each task:
- Has its own retry policy with exponential backoff
- Checks circuit breaker before execution
- Records success/failure for circuit breaker state
"""
import asyncio
from typing import Optional
from prefect import task
from prefect.states import Failed
from loguru import logger

from app.ai.character import extract_characters
from app.ai.plot import extract_plot_information
from app.ai.structure import extract_story_structure
from app.ai.world import extract_world_information
from app.ai.context import synthesize_chapter_context
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.world import WorldExtraction
from app.ai.models.context import CondensedChapterContext
from app.flows.circuit_breaker import gemini_breaker, CircuitOpenError
from app.config.prefect import DEFAULT_TASK_RETRIES, DEFAULT_TASK_RETRY_DELAYS, EXTRACTION_TASK_TIMEOUT


def _check_circuit_breaker() -> None:
    """Check circuit breaker and raise if open"""
    if not gemini_breaker.can_execute():
        ttr = gemini_breaker.time_to_recovery()
        raise CircuitOpenError("gemini-api", ttr or 0)


@task(
    name="extract-characters",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def extract_characters_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
) -> dict:
    """Extract character information from chapter"""
    _check_circuit_breaker()
    
    try:
        result: CharacterExtraction = await extract_characters(
            story_context, chapter_content, chapter_number, chapter_title
        )
        gemini_breaker.record_success()
        logger.debug(f"Chapter {chapter_number}: Character extraction complete")
        return result.model_dump()
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
        logger.error(f"Chapter {chapter_number}: Character extraction failed - {e}")
        raise


@task(
    name="extract-plot",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def extract_plot_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
) -> dict:
    """Extract plot information from chapter"""
    _check_circuit_breaker()
    
    try:
        result: PlotExtraction = await extract_plot_information(
            story_context, chapter_content, chapter_number, chapter_title
        )
        gemini_breaker.record_success()
        logger.debug(f"Chapter {chapter_number}: Plot extraction complete")
        return result.model_dump()
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
        logger.error(f"Chapter {chapter_number}: Plot extraction failed - {e}")
        raise


@task(
    name="extract-world",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def extract_world_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
) -> dict:
    """Extract world/setting information from chapter"""
    _check_circuit_breaker()
    
    try:
        result: WorldExtraction = await extract_world_information(
            story_context, chapter_content, chapter_number, chapter_title
        )
        gemini_breaker.record_success()
        logger.debug(f"Chapter {chapter_number}: World extraction complete")
        return result.model_dump()
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
        logger.error(f"Chapter {chapter_number}: World extraction failed - {e}")
        raise


@task(
    name="extract-structure",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def extract_structure_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
) -> dict:
    """Extract narrative structure from chapter"""
    _check_circuit_breaker()
    
    try:
        result: StructureExtraction = await extract_story_structure(
            story_context, chapter_content, chapter_number, chapter_title
        )
        gemini_breaker.record_success()
        logger.debug(f"Chapter {chapter_number}: Structure extraction complete")
        return result.model_dump()
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
        logger.error(f"Chapter {chapter_number}: Structure extraction failed - {e}")
        raise


@task(
    name="synthesize-context",
    retries=DEFAULT_TASK_RETRIES,
    retry_delay_seconds=DEFAULT_TASK_RETRY_DELAYS,
    timeout_seconds=EXTRACTION_TASK_TIMEOUT,
)
async def synthesize_context_task(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    character_extraction: dict,
    plot_extraction: dict,
    world_extraction: dict,
    structure_extraction: dict,
) -> dict:
    """Synthesize all extractions into condensed context"""
    _check_circuit_breaker()
    
    try:
        # Convert dicts back to models for synthesis
        char_model = CharacterExtraction.model_validate(character_extraction)
        plot_model = PlotExtraction.model_validate(plot_extraction)
        world_model = WorldExtraction.model_validate(world_extraction)
        struct_model = StructureExtraction.model_validate(structure_extraction)
        
        result: CondensedChapterContext = await synthesize_chapter_context(
            chapter_id, chapter_number, chapter_title, word_count,
            char_model, plot_model, world_model, struct_model
        )
        gemini_breaker.record_success()
        logger.debug(f"Chapter {chapter_number}: Context synthesis complete")
        return result.model_dump()
    except CircuitOpenError:
        raise
    except Exception as e:
        gemini_breaker.record_failure()
        logger.error(f"Chapter {chapter_number}: Context synthesis failed - {e}")
        raise


@task(
    name="save-chapter-extraction",
    retries=2,
    retry_delay_seconds=[5, 10],
)
async def save_chapter_extraction_task(
    chapter_id: str,
    character_extraction: dict,
    plot_extraction: dict,
    world_extraction: dict,
    structure_extraction: dict,
    context_synthesis: dict,
    word_count: int,
) -> None:
    """
    Save extraction results to database - CHECKPOINT.
    
    This task commits the chapter extraction independently,
    ensuring partial progress is preserved on failure.
    """
    from datetime import datetime
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.core.database import engine
    from app.models import Chapter
    from app.flows.circuit_breaker import database_breaker
    
    if not database_breaker.can_execute():
        ttr =  database_breaker.time_to_recovery()
        raise CircuitOpenError("postgres", ttr or 0)
    
    try:
        async with AsyncSession(engine) as db:
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            # Save all extraction results
            chapter.character_extraction = character_extraction
            chapter.plot_extraction = plot_extraction
            chapter.world_extraction = world_extraction
            chapter.structure_extraction = structure_extraction
            
            # Save synthesized context
            chapter.condensed_context = context_synthesis.get("condensed_text")
            chapter.timeline_context = context_synthesis.get("timeline_context")
            chapter.themes = context_synthesis.get("themes_present")
            chapter.emotional_arc = context_synthesis.get("emotional_arc")
            
            # Update metadata
            chapter.last_extracted_at = datetime.utcnow()
            chapter.last_extracted_word_count = word_count
            chapter.extraction_version = "2.0.0"  # Prefect version
            
            await db.commit()
            
        database_breaker.record_success()
        logger.info(f"✅ Chapter {chapter_id} extraction saved (checkpoint)")
        
    except CircuitOpenError:
        raise
    except Exception as e:
        database_breaker.record_failure()
        logger.error(f"Failed to save chapter {chapter_id} extraction: {e}")
        raise
