from src.data.models import Session
from datetime import datetime, timezone
from loguru import logger



async def cleanup_expired_sessions():
    """Remove expired sessions."""

    now = datetime.now(timezone.utc)
    total_deleted = await Session.filter(expires_at__lt=now).delete()

    if total_deleted > 0:
        logger.info("session.cleanup_complete", sessions_deleted=total_deleted)
