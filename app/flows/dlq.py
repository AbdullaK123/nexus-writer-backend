"""
Dead-Letter Queue (DLQ) service for handling failed jobs.

When a job exhausts all retries, it's recorded in the DLQ with full context
for manual review, debugging, and retry capability.

Features:
- Full input payload preservation for replay
- Error details and stack traces
- Manual and bulk retry capabilities
- Status tracking (pending, retried, resolved, ignored)
"""
import traceback
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.models import DeadLetterJob, DLQStatus
from app.core.database import engine


class DeadLetterService:
    """Service for managing dead-letter queue operations"""
    
    async def send_to_dlq(
        self,
        flow_run_id: str,
        flow_name: str,
        user_id: str,
        input_payload: dict,
        error: Exception,
        retry_count: int,
        task_name: Optional[str] = None,
        chapter_id: Optional[str] = None,
        story_id: Optional[str] = None,
    ) -> DeadLetterJob:
        """
        Record a failed job in the dead-letter queue.
        
        Args:
            flow_run_id: Prefect flow run ID
            flow_name: Name of the failed flow
            user_id: User who initiated the job
            input_payload: Original input parameters for replay
            error: The exception that caused the failure
            retry_count: How many retries were attempted
            task_name: Specific task that failed (if applicable)
            chapter_id: Related chapter (if applicable)
            story_id: Related story (if applicable)
            
        Returns:
            Created DeadLetterJob record
        """
        dlq_entry = DeadLetterJob(
            id=str(uuid4()),
            flow_run_id=flow_run_id,
            flow_name=flow_name,
            task_name=task_name,
            chapter_id=chapter_id,
            story_id=story_id,
            user_id=user_id,
            input_payload=input_payload,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            original_retry_count=retry_count,
            failed_at=datetime.utcnow(),
            status=DLQStatus.PENDING,
        )
        
        async with AsyncSession(engine) as db:
            db.add(dlq_entry)
            await db.commit()
            await db.refresh(dlq_entry)
        
        logger.warning(
            f"Job sent to DLQ: flow={flow_name}, "
            f"error={type(error).__name__}, "
            f"dlq_id={dlq_entry.id}"
        )
        
        # TODO: Send alert (Slack, email, etc.)
        await self._send_alert(dlq_entry)
        
        return dlq_entry
    
    async def _send_alert(self, dlq_entry: DeadLetterJob) -> None:
        """Send alert for DLQ entry (placeholder for Slack/email integration)"""
        # TODO: Implement alerting
        logger.error(
            f"🚨 DLQ ALERT: Job failed permanently\n"
            f"  Flow: {dlq_entry.flow_name}\n"
            f"  Error: {dlq_entry.error_type}: {dlq_entry.error_message}\n"
            f"  DLQ ID: {dlq_entry.id}\n"
            f"  User ID: {dlq_entry.user_id}"
        )
    
    async def get_dlq_jobs(
        self,
        status: Optional[DLQStatus] = None,
        flow_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeadLetterJob]:
        """Query DLQ jobs with optional filters"""
        async with AsyncSession(engine) as db:
            query = select(DeadLetterJob).order_by(DeadLetterJob.failed_at.desc())
            
            if status:
                query = query.where(DeadLetterJob.status == status)
            if flow_name:
                query = query.where(DeadLetterJob.flow_name == flow_name)
            if user_id:
                query = query.where(DeadLetterJob.user_id == user_id)
            
            query = query.limit(limit).offset(offset)
            
            result = await db.execute(query)
            return list(result.scalars().all())
    
    async def get_dlq_job_by_id(self, dlq_id: str) -> Optional[DeadLetterJob]:
        """Get a specific DLQ job by ID"""
        async with AsyncSession(engine) as db:
            return await db.get(DeadLetterJob, dlq_id)
    
    async def get_pending_count(self) -> int:
        """Get count of pending DLQ jobs"""
        async with AsyncSession(engine) as db:
            from sqlalchemy import func
            query = select(func.count(DeadLetterJob.id)).where(
                DeadLetterJob.status == DLQStatus.PENDING
            )
            result = await db.execute(query)
            return result.scalar() or 0
    
    async def mark_as_retried(
        self,
        dlq_id: str,
        new_flow_run_id: str,
    ) -> Optional[DeadLetterJob]:
        """Mark a DLQ job as retried with new flow run ID"""
        async with AsyncSession(engine) as db:
            dlq_job = await db.get(DeadLetterJob, dlq_id)
            if not dlq_job:
                return None
            
            dlq_job.status = DLQStatus.RETRIED
            dlq_job.resolved_at = datetime.utcnow()
            dlq_job.resolution_notes = f"Retried as flow_run_id: {new_flow_run_id}"
            
            await db.commit()
            await db.refresh(dlq_job)
            
            logger.info(f"DLQ job {dlq_id} marked as retried (new run: {new_flow_run_id})")
            return dlq_job
    
    async def resolve(
        self,
        dlq_id: str,
        resolved_by: str,
        status: DLQStatus,
        notes: Optional[str] = None,
    ) -> Optional[DeadLetterJob]:
        """Manually resolve a DLQ job"""
        if status not in [DLQStatus.RESOLVED, DLQStatus.IGNORED]:
            raise ValueError(f"Invalid resolution status: {status}")
        
        async with AsyncSession(engine) as db:
            dlq_job = await db.get(DeadLetterJob, dlq_id)
            if not dlq_job:
                return None
            
            dlq_job.status = status
            dlq_job.resolved_at = datetime.utcnow()
            dlq_job.resolved_by = resolved_by
            dlq_job.resolution_notes = notes
            
            await db.commit()
            await db.refresh(dlq_job)
            
            logger.info(f"DLQ job {dlq_id} resolved as {status.value} by {resolved_by}")
            return dlq_job
    
    async def bulk_retry_matching(
        self,
        flow_name: Optional[str] = None,
        error_type: Optional[str] = None,
        failed_after: Optional[datetime] = None,
    ) -> List[str]:
        """
        Get DLQ job IDs matching criteria for bulk retry.
        
        Returns list of DLQ IDs to retry (actual retry logic in provider).
        """
        async with AsyncSession(engine) as db:
            query = select(DeadLetterJob.id).where(
                DeadLetterJob.status == DLQStatus.PENDING
            )
            
            if flow_name:
                query = query.where(DeadLetterJob.flow_name == flow_name)
            if error_type:
                query = query.where(DeadLetterJob.error_type == error_type)
            if failed_after:
                query = query.where(DeadLetterJob.failed_at >= failed_after)
            
            result = await db.execute(query)
            return [row[0] for row in result.all()]


# Singleton instance
dlq_service = DeadLetterService()
