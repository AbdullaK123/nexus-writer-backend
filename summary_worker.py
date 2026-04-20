from tortoise import Tortoise
from src.app.dependencies.services import get_ai_provider
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs.ai import regenerate_stale_summaries
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config import config
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from aiocron import Cron, crontab
import asyncio
import signal
from pathlib import Path

HEARTBEAT_FILE = Path("/tmp/worker_heartbeat")

log = get_layer_logger(LAYER_APP)

@crontab(config.ai.regeneration_cron_expression, start=False)
async def regenerate_summaries():
    
    provider = get_ai_provider()

    try:
        await regenerate_stale_summaries(provider)
    except Exception:
        log.exception("cron.regenerate_stale_summaries.failed")
    finally:
        HEARTBEAT_FILE.touch()


def shutdown(loop: asyncio.AbstractEventLoop, cron: Cron) -> None:
    cron.stop()
    loop.stop()


async def main():

    await Tortoise.init(config=TORTOISE_ORM)
    log.info("summary_worker.started")

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
        await Tortoise.close_connections()
        log.info("summary_worker.stopped.")