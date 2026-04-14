from src.data.models import Session
from datetime import datetime, timezone
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)


async def cleanup_expired_sessions_batched():
    """Remove expired sessions in batches for better performance"""
    
    now = datetime.now(timezone.utc)
    batch_size = 1000
    total_deleted = 0
    
    while True:
        expired_sessions = await Session.filter(
            expires_at__lt=now
        ).limit(batch_size).values_list('session_id', flat=True)
        
        if not expired_sessions:
            break
        
        deleted_count = await Session.filter(
            session_id__in=list(expired_sessions)
        ).delete()
        
        total_deleted += deleted_count
        
        if len(expired_sessions) < batch_size:
            break
    
    if total_deleted > 0:
        log.info("session.cleanup_complete", sessions_deleted=total_deleted)