import asyncio
import signal

from tortoise import Tortoise

from src.app.dependencies.services import get_ai_provider
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs.service import poll_job_registry
from src.service.ai.extraction import generate_all_extractions
from src.infrastructure.config import config
from src.shared.utils.logging_context import LAYER_APP, get_layer_logger
from aiocron import Cron, crontab
from pathlib import Path

HEARTBEAT_FILE = Path("/tmp/worker_heartbeat")


log = get_layer_logger(LAYER_APP)


@poll_job_registry(
    job_name="extraction",
    on_started_message="Extraction in progress",
    on_completed_message="Extraction complete",
    on_failed_message="Extraction failed"
)
async def run_extractions(story_id: str, **kwargs) -> None:
    provider = get_ai_provider()
    await generate_all_extractions(provider, story_id)


@crontab(config.ai.extraction_cron_expression, start=False)
async def poll_for_extractions() -> None:
    try:
        await run_extractions()
    except Exception:
        log.exception("cron.run_extractions.failed")
    finally:
        HEARTBEAT_FILE.touch()


def shutdown(loop: asyncio.AbstractEventLoop, cron: Cron) -> None:
    cron.stop()
    loop.stop()

async def main():

    await Tortoise.init(config=TORTOISE_ORM)
    log.info("extraction_worker.started")

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
        await Tortoise.close_connections()
        log.info("extraction_worker.stopped")



if __name__ == "__main__":
    asyncio.run(main())







