from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from aiocron import crontab
from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure, get_ai_provider
from src.service.ai.summarization import regenerate_stale_summaries
from src.infrastructure.config.settings import config
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP

log = get_layer_logger(LAYER_APP)

@asynccontextmanager
async def lifespan(app: FastAPI):

    log.info("Lifecycle starting: initialising infrastructure")
    await init_infrastructure()

    provider = get_ai_provider()

    
    async def _run_regeneration():
        try:
            await regenerate_stale_summaries(provider)
        except Exception:
            log.exception("cron.regenerate_stale_summaries.failed")

    # to catch stale summaries during downtime
    asyncio.create_task(_run_regeneration())

    log.info("Summary Regenerator initialized...")
    cron = crontab(
        config.ai.regeneration_cron_expression,
        _run_regeneration
    )

    yield
    
    log.info("Shutting down Summary Regenerator... ")
    cron.stop()

    log.info("Lifecycle shutdown: releasing infrastructure")
    await shutdown_infrastructure()
