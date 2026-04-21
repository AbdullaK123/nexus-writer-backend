import asyncio
import signal

from tortoise import Tortoise

from src.app.dependencies.services import get_ai_provider
from src.infrastructure.ai.enums import JobType
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs.service import poll_job_registry
from src.service.ai.extraction import generate_extraction_by_type
from src.infrastructure.config import config
from aiocron import Cron, crontab
from pathlib import Path
from loguru import logger
from src.shared.utils.logging import configure_logger

configure_logger()

HEARTBEAT_FILE = Path("/tmp/extraction_worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30




async def heartbeat_loop() -> None:
    while True:
        HEARTBEAT_FILE.touch()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


@poll_job_registry(
    job_name="extraction",
    on_started_message="Extraction in progress",
    on_completed_message="Extraction complete",
    on_failed_message="Extraction failed"
)
async def run_extractions(story_id: str, extraction_type: str, **kwargs) -> None:
    provider = get_ai_provider()
    await generate_extraction_by_type(
        provider=provider,
        extraction_type=JobType(extraction_type),
        story_id=story_id
    )


@crontab(config.ai.extraction_cron_expression, start=False)
async def poll_for_extractions() -> None:
    try:
        await run_extractions()
    except Exception:
        logger.exception("cron.run_extractions.failed")
    finally:
        HEARTBEAT_FILE.touch()


def shutdown(loop: asyncio.AbstractEventLoop, cron: Cron) -> None:
    cron.stop()
    loop.stop()

async def main():

    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("extraction_worker.started")
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, 
            shutdown, 
            loop, 
            poll_for_extractions
        )

    poll_for_extractions.start()

    try:
        await asyncio.Event().wait()
    finally:
        heartbeat_task.cancel()
        await Tortoise.close_connections()
        logger.info("extraction_worker.stopped")



if __name__ == "__main__":
    asyncio.run(main())







