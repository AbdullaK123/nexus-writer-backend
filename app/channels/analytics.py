# app/channels/analytics.py - FIXED VERSION
from socketio.async_server import AsyncServer
from app.providers.analytics import get_analytics_provider
from app.schemas.analytics import WritingSession, WritingSessionEvent
from app.utils.decorators import log_errors
from app.core.redis import get_redis
from loguru import logger
import asyncio
import json

analytics = get_analytics_provider()
redis_client = get_redis()

# ✅ CLEAN: AsyncServer with no session management bullshit
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    logger=True,
    engineio_logger=True
)

def save_session_to_redis(sid: str, data: dict):
    """Save session data to Redis - SYNC and RELIABLE"""
    redis_key = f"analytics_session:{sid}"
    # ✅ CONVERT DATETIME TO ISO STRING FOR JSON SERIALIZATION
    serializable_data = {}
    for key, value in data.items():
        if hasattr(value, 'isoformat'):  # datetime object
            serializable_data[key] = value.isoformat()
        else:
            serializable_data[key] = value
    
    redis_client.setex(redis_key, 3600, json.dumps(serializable_data))  # 1 hour TTL
    logger.debug(f"💾 Saved session to Redis: {redis_key}")

def get_session_from_redis(sid: str) -> dict:
    """Get session data from Redis - SYNC and RELIABLE"""
    redis_key = f"analytics_session:{sid}"
    data = redis_client.get(redis_key)
    if data:
        logger.debug(f"📖 Retrieved session from Redis: {redis_key}")
        parsed_data = json.loads(data)
        # ✅ CONVERT ISO STRING BACK TO DATETIME
        from datetime import datetime
        if 'timestamp' in parsed_data:
            parsed_data['timestamp'] = datetime.fromisoformat(parsed_data['timestamp'])
        return parsed_data
    logger.debug(f"❌ No session found in Redis: {redis_key}")
    return None

def delete_session_from_redis(sid: str):
    """Delete session data from Redis - SYNC and RELIABLE"""
    redis_key = f"analytics_session:{sid}"
    deleted = redis_client.delete(redis_key)
    if deleted:
        logger.debug(f"🗑️ Deleted session from Redis: {redis_key}")

@sio.on('session_start', namespace='/analytics')
@log_errors
def handle_session_start(sid: str, session_start_data: dict):
    logger.info(
        "📝 Writing session start event received", 
        sid=sid, 
        extra={"event_type": "session_start"}
    )
    
    # Validate incoming data
    event = WritingSessionEvent(**session_start_data)
    
    logger.debug(
        "✅ Session data validated successfully", 
        session_id=event.sessionId,
        user_id=event.userId,
        story_id=event.storyId, 
        chapter_id=event.chapterId,
        initial_word_count=event.wordCount,
        sid=sid
    )
    
    # ✅ SAVE TO REDIS - SYNC AND BULLETPROOF
    save_session_to_redis(sid, event.model_dump())
    
    logger.success(
        "🚀 Writing session started and stored in Redis", 
        session_id=event.sessionId,
        user_id=event.userId,
        sid=sid,
        extra={"performance_tracking": True}
    )

@sio.on('session_end', namespace='/analytics')
@log_errors 
def handle_session_end(sid: str, session_end_data: dict):
    logger.info(
        "🏁 Writing session end event received", 
        sid=sid,
        extra={"event_type": "session_end"}
    )
    
    # Validate end data
    end_event = WritingSessionEvent(**session_end_data)
    
    logger.debug(
        "✅ End event data validated", 
        session_id=end_event.sessionId,
        final_word_count=end_event.wordCount,
        sid=sid
    )
    
    # ✅ GET FROM REDIS - SYNC AND BULLETPROOF
    start_data = get_session_from_redis(sid)
    
    if not start_data:
        logger.warning(
            "⚠️ No session start data found in Redis", 
            sid=sid,
            session_id=end_event.sessionId,
            extra={"data_consistency_issue": True}
        )
        return
    
    start_event = WritingSessionEvent(**start_data)
    
    # Calculate session metrics
    words_written = end_event.wordCount - start_event.wordCount
    duration_seconds = (end_event.timestamp - start_event.timestamp).total_seconds()
    duration_minutes = duration_seconds / 60
    
    logger.debug(
        "📊 Session metrics calculated", 
        session_id=end_event.sessionId,
        words_written=words_written,
        duration_minutes=round(duration_minutes, 2),
        duration_seconds=round(duration_seconds, 2),
        wpm=round(words_written / duration_minutes, 2) if duration_minutes > 0 else 0,
        sid=sid
    )
    
    # Create session record
    session = WritingSession(
        id=start_event.sessionId,
        started=start_event.timestamp,
        ended=end_event.timestamp,
        user_id=start_event.userId,
        story_id=start_event.storyId,
        chapter_id=start_event.chapterId,
        words_written=words_written
    )
    
    logger.info(
        "💾 Saving writing session to DuckDB", 
        session_id=session.id,
        user_id=session.user_id,
        words_written=words_written,
        duration_minutes=round(duration_minutes, 2),
        sid=sid,
        extra={"db_operation": True}
    )
    
    # ✅ ASYNC TASK FOR DUCKDB SAVE - FIRE AND FORGET WITH PROPER ERROR HANDLING
    loop = asyncio.get_event_loop()
    task = loop.create_task(save_to_duckdb_async(session, sid))
    
    # Add a callback to handle task completion without blocking
    task.add_done_callback(lambda t: handle_task_completion(t, session.id, sid))
    
    # ✅ CLEAN UP REDIS - SYNC
    delete_session_from_redis(sid)

def handle_task_completion(task, session_id: str, sid: str):
    """Handle the completion of the DuckDB save task"""
    try:
        # Check if the task completed successfully
        if task.exception() is None:
            logger.success(
                "🎯 Writing session successfully saved to DuckDB", 
                session_id=session_id,
                sid=sid,
                extra={"analytics_success": True, "performance_tracking": True}
            )
        else:
            # Log the actual exception
            exception = task.exception()
            logger.error(
                "❌ Failed to save session to DuckDB",
                session_id=session_id,
                error_type=type(exception).__name__,
                error_message=str(exception),
                sid=sid,
                extra={"analytics_failure": True}
            )
    except Exception as e:
        logger.error(
            "❌ Error in task completion handler",
            session_id=session_id,
            error=str(e),
            sid=sid
        )

async def save_to_duckdb_async(session: WritingSession, sid: str):
    """Save to DuckDB asynchronously - CLEAN VERSION"""
    try:
        saved_session = await analytics.write_session(session)
        # Success is logged in the task completion handler
        return saved_session
    except Exception as e:
        # Re-raise the exception so it's caught by the task completion handler
        logger.debug(f"Exception in save_to_duckdb_async: {e}")
        raise e

@sio.on('connect', namespace='/analytics')
@log_errors
def on_connect(sid, environ, auth=None):
    logger.info(
        "🔌 Client connected to analytics namespace", 
        sid=sid,
        user_agent=environ.get('HTTP_USER_AGENT', 'unknown'),
        origin=environ.get('HTTP_ORIGIN', 'unknown'),
        auth=auth,
        extra={"connection_event": True}
    )

@sio.on('disconnect', namespace='/analytics')
@log_errors
def on_disconnect(sid, reason):
    logger.info(
        "🔌 Client disconnected from analytics namespace", 
        sid=sid,
        reason=reason,
        extra={"connection_event": True}
    )
    
    # ✅ CHECK REDIS FOR INCOMPLETE SESSIONS - SYNC
    session_data = get_session_from_redis(sid)
    if session_data:
        logger.warning(
            "⚠️ Client disconnected with incomplete session - cleaning up Redis", 
            sid=sid,
            reason=reason,
            session_id=session_data.get('sessionId'),
            user_id=session_data.get('userId'),
            extra={"incomplete_session": True}
        )
        # Clean up the Redis session
        delete_session_from_redis(sid)