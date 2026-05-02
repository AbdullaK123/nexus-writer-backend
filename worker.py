from src.infrastructure.db.pool import init_pool, close_pool, get_pool
from src.data.repositories import (
    ChapterRepository,
    SceneRepository,
    SessionRepository,
    UserRepository,
)
from src.service.auth import AuthService
from src.service.embedding.service import EmbeddingService
from src.service.extraction import ExtractionService
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
    pool = get_pool()
    auth_service = AuthService(UserRepository(pool), SessionRepository(pool))
    try:
        await auth_service.cleanup_expired_sessions()
    except Exception:
        logger.exception("cron.cleanup_expired_sessions.failed")
    finally:
        HEARTBEAT_FILE.touch()


@crontab(config.jobs.scene_extraction_cron_expression, start=False)
async def run_reextraction_job():
    provider = build_ai_provider()
    pool = get_pool()
    chapter_repo = ChapterRepository(pool)
    scene_repo = SceneRepository(pool)
    extraction_service = ExtractionService(provider, chapter_repo, scene_repo)
    try:
        await extraction_service.regenerate_stale_batched()
    except Exception:
        logger.exception("cron.run_reextraction_job.failed")
    finally:
        HEARTBEAT_FILE.touch()


@crontab(config.jobs.scene_embedding_cron_expression, start=False)
async def run_embedding_job():
    provider = build_ai_provider()
    pool = get_pool()
    scene_repo = SceneRepository(pool)
    embedding_service = EmbeddingService(scene_repo, provider)
    try:
        await embedding_service.embed_pending_batched()
    except Exception:
        logger.exception("cron.run_embedding_job.failed")
    finally:
        HEARTBEAT_FILE.touch()


async def main():
    await init_pool()
    logger.info("worker.started")
    heartbeat_task = asyncio.create_task(heartbeat_loop())

    loop = asyncio.get_running_loop()
    crons = [run_session_cleanup, run_reextraction_job, run_embedding_job]

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, request_shutdown, crons)

    for cron in crons:
        cron.start()

    try:
        await shutdown_event.wait()
    finally:
        heartbeat_task.cancel()
        await close_pool()
        logger.info("worker.stopped")



if __name__ == "__main__":
    asyncio.run(main())