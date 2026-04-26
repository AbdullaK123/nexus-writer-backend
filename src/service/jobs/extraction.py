from src.data.models import Extraction
from src.data.models.enums import ExtractionType
from src.infrastructure.ai.providers.protocol import AIProvider
from src.infrastructure.config import config
from src.service.extraction import extract_scenes
from datetime import datetime, timezone, timedelta
from itertools import batched
import asyncio
from loguru import logger

async def regenerate_stale_extractions_batched(
    provider: AIProvider,
    batch_size: int = config.jobs.scene_extraction_batch_size
) -> None:

    total_reextracted = 0

    needs_reextraction_ids = (
        await Extraction
            .filter(
                needs_reextraction=True,
                extraction_type=ExtractionType.SCENES,
                updated_at__lte=datetime.now(timezone.utc) - timedelta(
                    seconds=config.jobs.scene_extraction_window_seconds
                )
            )
            .order_by("updated_at")
            .limit(4*batch_size)
            .values_list("chapter_id", flat=True)
    )

    for batch in batched(needs_reextraction_ids, batch_size):
        results = await asyncio.gather(
            *(extract_scenes(provider, cid) for cid in batch),
            return_exceptions=True
        )
        for cid, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.warning(
                    "extract_scenes.failed",
                    chapter_id=cid,
                    error=str(result)
                )
            else:
                total_reextracted += 1

    if total_reextracted > 0:
        logger.info("regenerate_stale_extractions_batched.complete", extractions_regenerated=total_reextracted, )

