from src.data.models.summary import Summary
from src.infrastructure.config import config
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE
from src.infrastructure.ai.providers.protocol import AIProvider
import asyncio

log = get_layer_logger(LAYER_SERVICE)

async def regenerate_stale_summaries(
    provider: AIProvider, 
    batch_size: int = config.ai.regeneration_batch_size
) -> None:

    stale_chapter_ids = await (
        Summary
            .filter(is_stale=True)
            .distinct()
            .limit(batch_size)
            .values_list("chapter_id", flat=True)
    )

    if not stale_chapter_ids:
        return

    results = await asyncio.gather(
        *(generate_all_summaries(provider, cid) for cid in stale_chapter_ids), #type: ignore
        return_exceptions=True
    )

    for chapter_id, result in zip(stale_chapter_ids, results):
        if isinstance(result, Exception):
            log.warning(
                "ai.regenerate_stale_summaries.regeneration_failed",
                chapter_id=chapter_id,
                error=str(result)
            )