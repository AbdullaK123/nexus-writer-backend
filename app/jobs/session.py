from app.models import Session
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from datetime import datetime
from loguru import logger


async def cleanup_expired_sessions_batched():
    """Remove expired sessions in batches for better performance"""
    
    async with AsyncSession(engine) as db:
        now = datetime.utcnow()
        batch_size = 1000
        total_deleted = 0
        
        while True:
            batch_query = (
                select(Session.session_id)
                .where(Session.expires_at < now)
                .limit(batch_size)
            )
            
            session_ids = (await db.execute(batch_query)).scalars().all()
            
            if not session_ids:
                break
            
            delete_query = delete(Session).where(Session.session_id.in_(session_ids))
            await db.execute(delete_query)
            await db.commit()
            
            batch_count = len(session_ids)
            total_deleted += batch_count
            
            if batch_count < batch_size:
                break
        
        if total_deleted > 0:
            logger.info(f"Session cleanup: {total_deleted} expired sessions removed")