"""
Tier 1: Individual AI extraction tasks with retry policies.

Each task:
- Has its own retry policy with exponential backoff
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
from app.config.prefect import DEFAULT_TASK_RETRIES, DEFAULT_TASK_RETRY_DELAYS, EXTRACTION_TASK_TIMEOUT
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import engine
from app.models import Chapter
from app.core.mongodb import MongoDB


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
) -> CharacterExtraction:
    """Extract character information from chapter"""
    result: CharacterExtraction = await extract_characters(
        story_context, chapter_content, chapter_number, chapter_title
    )
    logger.debug(f"Chapter {chapter_number}: Character extraction complete")
    return result


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
) -> PlotExtraction:
    """Extract plot information from chapter"""
    result: PlotExtraction = await extract_plot_information(
        story_context, chapter_content, chapter_number, chapter_title
    )
    logger.debug(f"Chapter {chapter_number}: Plot extraction complete")
    return result


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
) -> WorldExtraction:
    """Extract world/setting information from chapter"""
    result: WorldExtraction = await extract_world_information(
        story_context, chapter_content, chapter_number, chapter_title
    )
    logger.debug(f"Chapter {chapter_number}: World extraction complete")
    return result


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
) -> StructureExtraction:
    """Extract narrative structure from chapter"""
    result: StructureExtraction = await extract_story_structure(
        story_context, chapter_content, chapter_number, chapter_title
    )
    logger.debug(f"Chapter {chapter_number}: Structure extraction complete")
    return result


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
) -> CondensedChapterContext:
    """Synthesize all extractions into condensed context"""
    # Convert dicts back to models for synthesis
    char_model = CharacterExtraction.model_validate(character_extraction)
    plot_model = PlotExtraction.model_validate(plot_extraction)
    world_model = WorldExtraction.model_validate(world_extraction)
    struct_model = StructureExtraction.model_validate(structure_extraction)
    
    result: CondensedChapterContext = await synthesize_chapter_context(
        chapter_id, chapter_number, chapter_title, word_count,
        char_model, plot_model, world_model, struct_model
    )
    logger.debug(f"Chapter {chapter_number}: Context synthesis complete")
    return result


@task(
    name="save-chapter-extraction",
    retries=2,
    retry_delay_seconds=[5, 10],
)
async def save_chapter_extraction_task(
    chapter_id: str,
    chapter_number: int,
    character_extraction: CharacterExtraction,
    plot_extraction: PlotExtraction,
    world_extraction: WorldExtraction,
    structure_extraction: StructureExtraction,
    context_synthesis: CondensedChapterContext,
    word_count: int,
) -> None:
    """Save extraction results to both MongoDB and Postgres."""
    
    async with AsyncSession(engine) as db:
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")
        
        mongo_db = MongoDB.db
        if mongo_db is None:
            raise ValueError("MongoDB not connected")
        
        # Save to MongoDB — model_dump() handles all field serialization
        meta = {"chapter_id": chapter_id, "story_id": chapter.story_id, "chapter_number": chapter_number}

        await mongo_db.character_extractions.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **character_extraction.model_dump()},
            upsert=True
        )

        await mongo_db.plot_extractions.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **plot_extraction.model_dump()},
            upsert=True
        )

        await mongo_db.world_extractions.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **world_extraction.model_dump()},
            upsert=True
        )

        await mongo_db.structure_extractions.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **structure_extraction.model_dump()},
            upsert=True
        )

        await mongo_db.chapter_contexts.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **context_synthesis.model_dump()},
            upsert=True
        )
        
        logger.info(f"✅ Saved extractions to MongoDB for chapter {chapter_id}")
        
        # Save synthesized context to Postgres
        chapter.condensed_context = context_synthesis.condensed_text
        chapter.timeline_context = context_synthesis.timeline_context
        chapter.emotional_arc = context_synthesis.emotional_arc
        
        # Update metadata
        chapter.last_extracted_at = datetime.utcnow()
        chapter.last_extracted_word_count = word_count
        chapter.extraction_version = "2.0.0"
        
        await db.commit()
        
    logger.info(f"✅ Chapter {chapter_id} extraction saved (checkpoint)")