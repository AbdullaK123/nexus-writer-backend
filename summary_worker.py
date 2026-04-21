from tortoise import Tortoise
from src.app.dependencies.services import get_ai_provider
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs.ai import regenerate_stale_summaries
from src.infrastructure.config import config
from aiocron import Cron, crontab
import asyncio
import signal
from pathlib import Path
from loguru import logger
from src.shared.utils.logging import configure_logger

configure_logger()

HEARTBEAT_FILE = Path("/tmp/summary_worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30

async def heartbeat_loop() -> None:
    while True:
        HEARTBEAT_FILE.touch()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

@crontab(config.ai.regeneration_cron_expression, start=False)
async def regenerate_summaries():
    
    provider = get_ai_provider()

    try:
        await regenerate_stale_summaries(provider)
    except Exception:
        logger.exception("cron.regenerate_stale_summaries.failed")
    finally:
        HEARTBEAT_FILE.touch()


def shutdown(loop: asyncio.AbstractEventLoop, cron: Cron) -> None:
    cron.stop()
    loop.stop()


async def main():

    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("summary_worker.started")
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            shutdown,
            loop,
            regenerate_summaries
        )

    regenerate_summaries.start()

    try:
        await asyncio.Event().wait()
    finally:
        heartbeat_task.cancel()
        await Tortoise.close_connections()
        logger.info("summary_worker.stopped")


if __name__ == "__main__":
    asyncio.run(main())