from app.models import Session
from app.core.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.utils.logging import log_background_job
from app.utils.retry import db_retry
from sqlmodel import select, delete
from datetime import datetime
from loguru import logger

@log_background_job
@db_retry(max_retries=3)
async def cleanup_expired_sessions():
    """Remove expired user sessions from database"""
    
    async with AsyncSession(engine) as db:
        # Get current time for comparison
        now = datetime.utcnow()
        
        logger.debug("Starting session cleanup for expired sessions before {cutoff_time}", cutoff_time=now)
        
        # Count expired sessions first (for logging)
        count_query = select(Session).where(Session.expires_at < now)
        expired_sessions = (await db.execute(count_query)).scalars().all()
        expired_count = len(expired_sessions)
        
        if expired_count == 0:
            logger.debug("No expired sessions found")
            return
        
        # Delete expired sessions efficiently
        delete_query = delete(Session).where(Session.expires_at < now)
        result = await db.execute(delete_query)
        await db.commit()
        
        logger.success(
            "Cleaned up {count} expired sessions",
            count=expired_count,
            cutoff_time=now,
            operation="session_cleanup"
        )

# Alternative version with batch processing for large datasets
@log_background_job
@db_retry(max_retries=3)
async def cleanup_expired_sessions_batched():
    """Remove expired sessions in batches for better performance"""
    
    async with AsyncSession(engine) as db:
        now = datetime.utcnow()
        batch_size = 1000
        total_deleted = 0
        
        logger.info("Starting batched session cleanup")
        
        while True:
            # Get batch of expired session IDs
            batch_query = (
                select(Session.session_id)
                .where(Session.expires_at < now)
                .limit(batch_size)
            )
            
            session_ids = (await db.execute(batch_query)).scalars().all()
            
            if not session_ids:
                break  # No more expired sessions
            
            # Delete this batch
            delete_query = delete(Session).where(Session.session_id.in_(session_ids))
            await db.execute(delete_query)
            await db.commit()
            
            batch_count = len(session_ids)
            total_deleted += batch_count
            
            logger.debug("Deleted batch of {batch_count} sessions", batch_count=batch_count)
            
            # If we got less than batch_size, we're done
            if batch_count < batch_size:
                break
        
        logger.success(
            "Batched session cleanup completed: {total} sessions removed",
            total=total_deleted,
            cutoff_time=now
        )

# Cleanup with additional metadata logging
@log_background_job
@db_retry(max_retries=3)  
async def cleanup_expired_sessions_with_analytics():
    """Session cleanup with detailed analytics logging"""
    
    async with AsyncSession(engine) as db:
        now = datetime.utcnow()
        
        # Get detailed info about sessions being deleted
        expired_query = (
            select(Session)
            .where(Session.expires_at < now)
        )
        expired_sessions = (await db.execute(expired_query)).scalars().all()
        
        if not expired_sessions:
            logger.debug("No expired sessions to clean up")
            return
        
        # Analytics before deletion
        user_ids = {session.user_id for session in expired_sessions}
        oldest_session = min(session.expires_at for session in expired_sessions)
        
        logger.info(
            "Cleaning up {count} expired sessions from {users} users, oldest expired: {oldest}",
            count=len(expired_sessions),
            users=len(user_ids),
            oldest=oldest_session
        )
        
        # Delete expired sessions
        delete_query = delete(Session).where(Session.expires_at < now)
        await db.execute(delete_query)
        await db.commit()
        
        logger.success(
            "Session cleanup completed: {count} sessions removed",
            count=len(expired_sessions),
            affected_users=len(user_ids),
            operation="session_cleanup"
        )