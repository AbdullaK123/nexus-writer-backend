from src.data.models.summary import Summary
from src.infrastructure.config import config
from src.service.ai.summarization import generate_all_summaries
from src.infrastructure.ai.providers.protocol import AIProvider
import asyncio
from loguru import logger



async def regenerate_stale_summaries(
    provider: AIProvider, 
    batch_size: int = config.ai.regeneration_batch_size
) -> None:
    
    stale_chapter_ids = await (
        Summary.filter(is_stale=True)
        .distinct()
        .limit(batch_size)
        .values_list("chapter_id", flat=True)
    )

    if not stale_chapter_ids:
        logger.debug("ai.regenerate_stale_summaries.no_work", batch_size=batch_size)
        return

    logger.info(
        "ai.regenerate_stale_summaries.start",
        batch_size=batch_size,
        chapter_count=len(stale_chapter_ids),
    )

    results = await asyncio.gather(
        *(generate_all_summaries(provider, cid) for cid in stale_chapter_ids),  # type: ignore
        return_exceptions=True,
    )

    failed = 0
    for chapter_id, result in zip(stale_chapter_ids, results):
        if isinstance(result, Exception):
            failed += 1
            logger.warning(
                "ai.regenerate_stale_summaries.regeneration_failed",
                chapter_id=chapter_id,
                error=str(result),
            )

    logger.info(
        "ai.regenerate_stale_summaries.done",
        chapter_count=len(stale_chapter_ids),
        failed=failed,
    )
