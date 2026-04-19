from src.app.dependencies.services import get_ai_provider
from src.service.jobs.ai import regenerate_stale_summaries
from src.service.jobs.session import cleanup_expired_sessions_batched
from src.infrastructure.config import config
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from aiocron import crontab

log = get_layer_logger(LAYER_APP)



@crontab(config.ai.regeneration_cron_expression, start=False)    
async def regenerate_summaries():

    provider = get_ai_provider()

    try:
        await regenerate_stale_summaries(provider)
    except Exception:
        log.exception("cron.regenerate_stale_summaries.failed")


@crontab(config.jobs.session_cleanup_cron_expression, start=False)
async def cleanup_expired_sessions():
    try:
        await cleanup_expired_sessions_batched()
    except Exception:
        log.exception("cron.cleanup_expired_sessions.failed")


async def run_all_jobs():
    provider = get_ai_provider()
    batch_size = config.jobs.session_cleanup_batch_size
    log.info("Regenerating stale summaries...")
    await regenerate_stale_summaries(provider)
    log.info("Cleaning up expired sessions...")
    await cleanup_expired_sessions_batched(batch_size)



def start_all_jobs():
    log.info("Summary Regenerator initialized...")
    regenerate_summaries.start()
    log.info("Session cleaner initialized...")
    cleanup_expired_sessions.start()


def stop_all_jobs():
    log.info("Shutting down Summary Regenerator... ")
    regenerate_summaries.stop()
    log.info("Shutting down session cleaner...")
    cleanup_expired_sessions.stop()