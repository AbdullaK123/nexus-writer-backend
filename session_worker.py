from tortoise import Tortoise
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config import config
from aiocron import Cron, crontab
import asyncio
import signal
from pathlib import Path
from loguru import logger
from src.shared.utils.logging import configure_logger

configure_logger()

HEARTBEAT_FILE = Path("/tmp/session_worker_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = 30



async def heartbeat_loop() -> None:
    while True:
        HEARTBEAT_FILE.touch()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

@crontab(config.jobs.session_cleanup_cron_expression, start=False)
async def cleanup_expired_sessions():
    try:
        await cleanup_expired_sessions_batched()
    except Exception:
        logger.exception("cron.cleanup_expired_sessions.failed")
    finally:
        HEARTBEAT_FILE.touch()

def shutdown(loop: asyncio.AbstractEventLoop, cron: Cron) -> None:
    cron.stop()
    loop.stop()
  

async def main():

    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("session_worker.started")
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, 
            shutdown, 
            loop, 
            cleanup_expired_sessions
        )

    cleanup_expired_sessions.start()

    try:
        await asyncio.Event().wait()
    finally:
        heartbeat_task.cancel()
        await Tortoise.close_connections()
        logger.info("session_worker.stopped")



if __name__ == "__main__":
    asyncio.run(main())