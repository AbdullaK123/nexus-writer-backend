"""
arq worker entry point for running background jobs in a separate container.

This worker processes jobs enqueued via the arq Redis queue.
It should be run in a dedicated container separate from the API server.
"""
from arq import func
from arq.connections import RedisSettings
from tortoise import Tortoise

from src.infrastructure.config import settings, config
from src.infrastructure.config.logging import setup_logging
from src.infrastructure.db.mongodb import MongoDB
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.infrastructure.redis.job_registry import JobRegistry
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from src.service.flows.extraction.chapter_flow import extract_single_chapter
from src.service.flows.extraction.reextraction_flow import reextract_chapters
from src.service.flows.line_edits.flow import line_edits_job

from dotenv import load_dotenv

load_dotenv()
setup_logging()

log = get_layer_logger(LAYER_APP)


async def startup(ctx: dict) -> None:
    """Initialise Tortoise, MongoDB, and JobRegistry before processing jobs."""
    log.info("worker.starting")
    await Tortoise.init(config=TORTOISE_ORM)
    await MongoDB.connect(settings.mongodb_url, config.mongo.database_name)
    ctx["registry"] = JobRegistry(ctx["redis"])
    log.info("worker.infra_ready")


async def shutdown(ctx: dict) -> None:
    """Tear down infrastructure on worker shutdown."""
    log.info("worker.shutting_down")
    await MongoDB.close()
    await Tortoise.close_connections()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_broker_url)
    on_startup = startup
    on_shutdown = shutdown
    functions = [
        func(extract_single_chapter, name="extract_single_chapter", timeout=config.worker.chapter_flow_timeout),
        func(line_edits_job, name="line_edits_job", timeout=config.worker.extraction_task_timeout),
        func(reextract_chapters, name="reextract_chapters", timeout=config.worker.chapter_flow_timeout * 10),
    ]
    max_jobs = config.worker.max_jobs
    allow_abort_jobs = True
