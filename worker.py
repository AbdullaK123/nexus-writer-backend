from tortoise import Tortoise
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs import cleanup_expired_sessions, regenerate_stale_extractions_batched
from src.infrastructure.config import config
from src.app.dependencies import build_ai_provider
from aiocron import Cron, crontab
import asyncio
import signal
from pathlib import Path
from loguru import logger
from src.shared.utils.logging import configure_logger

configure_logger()

HEARTBEAT_FILE = Path("/tmp/worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30

shutdown_event = asyncio.Event()


async def heartbeat_loop() -> None:
    while True:
        HEARTBEAT_FILE.touch()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


def request_shutdown(crons: list[Cron]) -> None:
    for cron in crons:
        cron.stop()
    shutdown_event.set()


@crontab(config.jobs.session_cleanup_cron_expression, start=False)
async def run_session_cleanup():
    try:
        await cleanup_expired_sessions()
    except Exception:
        logger.exception("cron.cleanup_expired_sessions.failed")
    finally:
        HEARTBEAT_FILE.touch()


@crontab(config.jobs.scene_extraction_cron_expression, start=False)
async def run_reextraction_job():
    provider = build_ai_provider()
    try:
        await regenerate_stale_extractions_batched(provider)
    except Exception:
        logger.exception("cron.run_reextraction_job.failed")
    finally:
        HEARTBEAT_FILE.touch()


async def main():
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("worker.started")
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    loop = asyncio.get_running_loop()
    crons = [run_session_cleanup, run_reextraction_job]

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, request_shutdown, crons)

    for cron in crons:
        cron.start()

    try:
        await shutdown_event.wait()
    finally:
        heartbeat_task.cancel()
        await Tortoise.close_connections()
        logger.info("worker.stopped")



if __name__ == "__main__":
    asyncio.run(main())