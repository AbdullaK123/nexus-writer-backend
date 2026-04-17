from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.service.flows.extraction.chapter_flow import _run_extraction
from src.infrastructure.redis.job_registry import JobRegistry, RegistryStatus
from typing import List
from src.data.models import Chapter, Story
from src.data.schemas.jobs import (
    JobType,
    ReextractionEventData,
    ReextractionProgressData,
    ReextractionCompleteData,
)
from src.infrastructure.config import settings
from src.service.flows.publisher import FlowPublisher
from src.shared.utils.html import html_to_plain_text


async def _run_reextraction(
    registry: JobRegistry,
    job_run_id: str,
    *,
    story_id: str,
    chapter_ids: List[str],
    user_id: str = "",
):
    """Core reextraction logic — re-extract chapters in sequence after deletion."""

    pub = FlowPublisher[ReextractionEventData](
        redis_url=settings.redis_url,
        user_id=user_id,
        story_id=story_id,
        job_type=JobType.REEXTRACTION,
        total_steps=len(chapter_ids),
        job_run_id=job_run_id,
    )
    try:
        await pub.flow_started()

        # Get story
        story = await Story.get_or_none(id=story_id)
        if not story or not story.path_array:
            await pub.flow_failed(message=f"Story {story_id} not found or has no chapters")
            raise ValueError(f"Story {story_id} not found or has no chapters")
        
        log.info("reextraction.started", story_id=story_id, chapter_count=len(chapter_ids))
        
        # Process each chapter IN ORDER (chapter_ids is already ordered from path_array)
        for chapter_id in chapter_ids:
            # Get chapter
            chapter = await Chapter.get_or_none(id=chapter_id)
            if not chapter:
                log.warning("reextraction.chapter_not_found: skipping", chapter_id=chapter_id)
                continue
            
            chapter_number = Chapter.get_chapter_number(chapter.id, story.path_array)
            if chapter_number is None:
                log.warning("reextraction.no_chapter_number: skipping", chapter_id=chapter_id)
                continue
            
            log.info("reextraction.processing_chapter", chapter_number=chapter_number, chapter_id=chapter_id, title=chapter.title)
            await pub.task_started(f"chapter_{chapter_number}", message=f"Extracting chapter {chapter_number}")
            
            # Extract — predecessor wait + context building happen inside _run_extraction
            result = await _run_extraction(
                registry,
                f"{job_run_id}:sub:{chapter.id}",
                chapter_id=chapter.id,
                chapter_number=chapter_number,
                chapter_title=chapter.title,
                word_count=chapter.word_count,
                story_id=story_id,
                story_path_array=story.path_array,
                content=html_to_plain_text(chapter.content),
                user_id=user_id,
            )
            
            await pub.task_complete(
                f"chapter_{chapter_number}",
                data=ReextractionProgressData(
                    chapter_id=chapter.id,
                    chapter_number=chapter_number,
                    is_partial=result.is_partial,
                ),
            )
            log.info("reextraction.chapter_complete", chapter_number=chapter_number)
        
        log.info("reextraction.complete", story_id=story_id, chapter_count=len(chapter_ids))
        await pub.flow_complete(data=ReextractionCompleteData(chapters_processed=len(chapter_ids)))
    finally:
        await pub.close()


async def reextract_chapters(ctx: dict, **kwargs):
    """arq job entry point — wraps _run_reextraction with registry status tracking."""
    registry: JobRegistry = ctx["registry"]
    job_id: str = ctx["job_id"]
    await registry.set_status(job_id, RegistryStatus.RUNNING)
    try:
        await _run_reextraction(registry, job_id, **kwargs)
        await registry.set_status(job_id, RegistryStatus.COMPLETE)
    except Exception:
        await registry.set_status(job_id, RegistryStatus.FAILED)
        raise