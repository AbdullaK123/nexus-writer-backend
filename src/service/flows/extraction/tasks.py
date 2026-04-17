"""
Tier 1: Individual AI extraction tasks with retry policies.

Each task:
- Has its own retry policy with exponential backoff
"""
import asyncio
from typing import Optional

from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.service.ai.character import extract_characters
from src.service.ai.plot import extract_plot_information
from src.service.ai.structure import extract_story_structure
from src.service.ai.world import extract_world_information
from src.service.ai.context import synthesize_chapter_context
from src.data.models.ai.character import CharacterExtraction
from src.data.models.ai.plot import PlotExtraction
from src.data.models.ai.structure import StructureExtraction
from src.data.models.ai.world import WorldExtraction
from src.data.models.ai.context import CondensedChapterContext
from src.infrastructure.config import config
from datetime import datetime, timezone
from src.data.models import Chapter
from src.infrastructure.db.mongodb import MongoDB


async def extract_characters_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> CharacterExtraction:
    """Extract character information from chapter"""
    log.debug("task.character_extraction.start", chapter_number=chapter_number, story_id=story_id)
    result: CharacterExtraction = await extract_characters(
        story_context, chapter_content, chapter_number, chapter_title,
        story_id=story_id,
    )
    log.debug("task.character_extraction_complete", chapter_number=chapter_number)
    return result


async def extract_plot_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> PlotExtraction:
    """Extract plot information from chapter"""
    log.debug("task.plot_extraction.start", chapter_number=chapter_number, story_id=story_id)
    result: PlotExtraction = await extract_plot_information(
        story_context, chapter_content, chapter_number, chapter_title,
        story_id=story_id,
    )
    log.debug("task.plot_extraction_complete", chapter_number=chapter_number)
    return result


async def extract_world_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> WorldExtraction:
    """Extract world/setting information from chapter"""
    log.debug("task.world_extraction.start", chapter_number=chapter_number, story_id=story_id)
    result: WorldExtraction = await extract_world_information(
        story_context, chapter_content, chapter_number, chapter_title,
        story_id=story_id,
    )
    log.debug("task.world_extraction_complete", chapter_number=chapter_number)
    return result


async def extract_structure_task(
    story_context: str,
    chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> StructureExtraction:
    """Extract narrative structure from chapter"""
    log.debug("task.structure_extraction.start", chapter_number=chapter_number, story_id=story_id)
    result: StructureExtraction = await extract_story_structure(
        story_context, chapter_content, chapter_number, chapter_title,
        story_id=story_id,
    )
    log.debug("task.structure_extraction_complete", chapter_number=chapter_number)
    return result


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
        char_model, plot_model, world_model, struct_model,
    )
    log.debug("task.context_synthesis_complete", chapter_number=chapter_number)
    return result


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
    
    chapter = await Chapter.get_or_none(id=chapter_id)
    if not chapter:
        raise ValueError(f"Chapter {chapter_id} not found")
    
    mongo_db = MongoDB.db
    if mongo_db is None:
        raise ValueError("MongoDB not connected")
    
    # Save synthesized context to Postgres FIRST (cheaper to retry if Mongo fails)
    chapter.condensed_context = context_synthesis.condensed_text
    chapter.timeline_context = context_synthesis.timeline_context
    chapter.emotional_arc = context_synthesis.emotional_arc
    
    # Update metadata
    chapter.last_extracted_at = datetime.now(timezone.utc)
    chapter.last_extracted_word_count = word_count
    chapter.extraction_version = "2.0.0"
    
    await chapter.save(update_fields=[
        'condensed_context', 'timeline_context', 'emotional_arc',
        'last_extracted_at', 'last_extracted_word_count', 'extraction_version'
    ])
    
    log.info("task.extraction_checkpoint_saved", chapter_id=chapter_id, chapter_number=chapter_number)

    # Save to MongoDB — model_dump() handles all field serialization
    # Done after Postgres so that last_extracted_at is set even if Mongo fails.
    # Mongo writes are idempotent (upsert), so retrying the task is safe.
    meta = {
        "chapter_id": chapter_id, 
        "story_id": chapter.story_id,  # type: ignore[attr-defined]
        "user_id": chapter.user_id,  # type: ignore[attr-defined]
        "chapter_number": chapter_number
    }

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
    
    log.info("task.extractions_saved_mongo", chapter_id=chapter_id)