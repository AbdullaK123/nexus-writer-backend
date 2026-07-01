"""Scene extraction service.

ExtractionService:
  - extract_scenes(chapter_id):
      1. Read the chapter via ChapterRepository.get_for_system.
      2. Run the LLM (with quote-validation retries) to get a SceneExtraction.
      3. Atomically replace this chapter's scene rows AND clear the staleness
         flag on the chapter — both inside one transaction so a crash mid-write
         can't leave half-extracted state behind.
  - regenerate_stale_batched(batch_size):
      Sweep stale chapters (oldest first), in batches, calling extract_scenes
      per chapter. Failures are logged and skipped — the batch continues.

scenes_are_stale (module-level):
  Pure function. Given a list of Scenes (already in the DB) and the chapter's
  current plain-text content, returns True if any start/end quote no longer
  matches verbatim — i.e. the user edited the chapter and the existing
  extraction is now lying about scene boundaries.
"""
import asyncio
from itertools import batched
from typing import Any, Iterable

from loguru import logger

from src.data.repositories import ChapterRepository, SceneRepository
from src.data.schemas import SceneExtraction
from src.infrastructure.ai import AIProvider, SCENE_EXTRACTION_PROMPT
from src.infrastructure.config import config
from src.service.exceptions import InternalError, NotFoundError
from src.service.utils.decorators import handle_service_errors
from src.shared.utils.html import html_to_plain_text


def _validate_extraction(
    extraction: SceneExtraction, 
    content: str,
) -> list[str]:
    errors = []
    for scene in extraction.scenes:
        if scene.start_quote not in content:
            errors.append(f"start_quote not found verbatim: {scene.start_quote!r}")
        if scene.end_quote not in content:
            errors.append(f"end_quote not found verbatim: {scene.end_quote!r}")
        if scene.pov not in scene.mentioned_entities:
            errors.append(f"pov '{scene.pov}' not in mentioned_entities")
    return errors


async def _extract_with_feedback(
    provider: AIProvider,
    chapter_content: str
) -> SceneExtraction:
    
    feedback: list[str] = []
    
    for _ in range(config.ai.max_retries):
        prompt = chapter_content
        if feedback:
            corrections = "\n".join(f"- {f}" for f in feedback)
            prompt = (
                f"{chapter_content}\n\n"
                f"<previous_extraction_errors>\n"
                f"Your previous extraction had these problems:\n"
                f"{corrections}\n"
                f"Fix them in this attempt.\n"
                f"</previous_extraction_errors>"
            )
        
        extraction = await provider.extract(
            system_prompt=SCENE_EXTRACTION_PROMPT,
            text=prompt,
            max_tokens=config.ai.scene_extraction_max_tokens,
            schema=SceneExtraction,
        )
        
        errors = _validate_extraction(extraction, chapter_content)
        if not errors:
            return extraction
        
        feedback.extend(errors)
    
    raise InternalError(f"Failed after {config.ai.max_retries} attempts: {feedback}")


def scenes_are_stale(scenes: Iterable[Any], chapter_content: str) -> bool:
    """True if any scene's start/end quote no longer appears verbatim in the
    current chapter text. Duck-typed on `start_quote`/`end_quote` so callers
    can pass either Scene (LLM output) or SceneRow (DB row)."""
    for scene in scenes:
        if scene.start_quote not in chapter_content:
            return True
        if scene.end_quote not in chapter_content:
            return True
    return False


class ExtractionService:
    def __init__(
        self,
        provider: AIProvider,
        chapter_repo: ChapterRepository,
        scene_repo: SceneRepository,
    ) -> None:
        self._provider = provider
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo

    @handle_service_errors
    async def extract_scenes(self, chapter_id: str) -> None:
        chapter = await self._chapter_repo.get_for_system(chapter_id)
        if chapter is None:
            raise NotFoundError("Chapter not found")

        plain_text = html_to_plain_text(chapter.content)

        extraction = await _extract_with_feedback(
            provider=self._provider, chapter_content=plain_text,
        )

        async with self._scene_repo.pool.acquire() as conn:
            async with conn.transaction():
                await self._scene_repo.replace_for_chapter(
                    chapter_id=chapter.id,
                    story_id=chapter.story_id,
                    user_id=chapter.user_id,
                    scenes=extraction.scenes,
                    executor=conn,
                )
                await self._scene_repo.mark_chapter_extracted(
                    chapter.id, executor=conn,
                )

    async def regenerate_stale_batched(
        self,
        batch_size: int = config.jobs.scene_extraction_batch_size,
    ) -> None:
        """Sweep up to `4 * batch_size` stale chapters in one query, then
        re-extract them in batches concurrently. Per-chapter failures are
        logged and skipped."""
        total_reextracted = 0

        stale_chapter_ids = await self._scene_repo.list_stale_chapter_ids(
            window_seconds=config.jobs.scene_extraction_window_seconds,
            limit=4 * batch_size,
        )

        for batch in batched(stale_chapter_ids, batch_size):
            results = await asyncio.gather(
                *(self.extract_scenes(cid) for cid in batch),
                return_exceptions=True,
            )
            for cid, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.warning(
                        "extract_scenes.failed",
                        chapter_id=cid, error=str(result),
                    )
                else:
                    total_reextracted += 1

        if total_reextracted > 0:
            logger.info(
                "regenerate_stale_extractions_batched.complete",
                extractions_regenerated=total_reextracted,
            )
