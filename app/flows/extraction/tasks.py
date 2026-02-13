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
from app.ai.models.character import CharacterExtraction, ChapterCharacterExtraction
from app.ai.models.plot import PlotExtraction, ChapterPlotExtraction
from app.ai.models.structure import StructureExtraction, ChapterStructureExtraction
from app.ai.models.world import WorldExtraction, ChapterWorldExtraction
from app.ai.models.context import CondensedChapterContext, ChapterContext
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
        
        # Save to MongoDB (new) - use replace_one with upsert for unique constraint
        await mongo_db.character_extractions.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "chapter_number": chapter_number,
                "characters_present": [c.model_dump() for c in character_extraction.characters_present],
                "character_actions": [a.model_dump() for a in character_extraction.character_actions],
                "character_snapshots": [s.model_dump() for s in character_extraction.character_snapshots],
                "dialogue_samples": [d.model_dump() for d in character_extraction.dialogue_samples],
                "trait_claims": [t.model_dump() for t in character_extraction.trait_claims]
            },
            upsert=True
        )
        
        await mongo_db.plot_extractions.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "chapter_number": chapter_number,
                "events": [e.model_dump() for e in plot_extraction.events],
                "plot_threads": [t.model_dump() for t in plot_extraction.plot_threads],
                "foreshadowing": [f.model_dump() for f in plot_extraction.foreshadowing],
                "story_questions": [q.model_dump() for q in plot_extraction.story_questions],
                "causal_chains": [c.model_dump() for c in plot_extraction.causal_chains],
                "callbacks": [cb.model_dump() for cb in plot_extraction.callbacks],
                "deus_ex_machina_risks": [d.model_dump() for d in plot_extraction.deus_ex_machina_risks]
            },
            upsert=True
        )
        
        await mongo_db.world_extractions.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "chapter_number": chapter_number,
                "locations": [l.model_dump() for l in world_extraction.locations],
                "world_rules": [r.model_dump() for r in world_extraction.world_rules],
                "rule_violations": [rv.model_dump() for rv in world_extraction.rule_violations],
                "timeline_markers": [t.model_dump() for t in world_extraction.timeline_markers],
                "chapter_timespan": world_extraction.chapter_timespan.model_dump() if world_extraction.chapter_timespan else None,
                "injuries": [i.model_dump() for i in world_extraction.injuries],
                "travel_events": [te.model_dump() for te in world_extraction.travel_events],
                "cultural_elements": [c.model_dump() for c in world_extraction.cultural_elements],
                "factual_claims": [f.model_dump() for f in world_extraction.factual_claims],
                "sensory_details": world_extraction.sensory_details
            },
            upsert=True
        )
        
        await mongo_db.structure_extractions.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "chapter_number": chapter_number,
                "pacing": structure_extraction.pacing.model_dump(),
                "scenes": [s.model_dump() for s in structure_extraction.scenes],
                "themes": [t.model_dump() for t in structure_extraction.themes],
                "emotional_beats": [e.model_dump() for e in structure_extraction.emotional_beats],
                "structural_role": structure_extraction.structural_role,
                "show_vs_tell_ratio": structure_extraction.show_vs_tell_ratio
            },
            upsert=True
        )

        await mongo_db.chapter_contexts.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": chapter.story_id,
                "chapter_number": chapter_number,
                "timeline_context": context_synthesis.timeline_context,
                "entities_summary": context_synthesis.entities_summary,
                "events_summary": context_synthesis.events_summary,
                "character_developments": context_synthesis.character_developments,
                "plot_progression": context_synthesis.plot_progression,
                "worldbuilding_additions": context_synthesis.worldbuilding_additions,
                "themes_present": context_synthesis.themes_present,
                "emotional_arc": context_synthesis.emotional_arc,
                "word_count": context_synthesis.word_count,
                "estimated_reading_time_minutes": context_synthesis.estimated_reading_time_minutes,
                "condensed_text": context_synthesis.condensed_text
            },
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