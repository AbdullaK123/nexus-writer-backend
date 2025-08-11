# app/channels/analytics.py - FIXED VERSION
from socketio.async_server import AsyncServer
from app.providers.analytics import AnalyticsProvider
from app.schemas.analytics import WritingSession, WritingSessionEvent
from app.utils.decorators import log_errors
from loguru import logger

analytics = AnalyticsProvider()

# FIX: Explicitly set async_mode='asgi' and configure CORS
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    logger=True,
    engineio_logger=True
)

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
    
    # Store as dict (Socket.IO sessions work with JSON-serializable data)
    # Use save_session as a regular function - AsyncServer handles the async internally
    sio.save_session(sid, event.model_dump())
    
    logger.success(
        "🚀 Writing session started and stored", 
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
    
    # Get start data (will be a dict)
    start_data = sio.get_session(sid)
    
    if not start_data:
        logger.warning(
            "⚠️ No session start data found for sid", 
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
    
    # This will run in a background thread automatically
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    saved_session = loop.run_until_complete(analytics.write_session(session))
    loop.close()
    
    logger.success(
        "🎯 Writing session successfully saved", 
        session_id=saved_session.id,
        user_id=saved_session.user_id,
        story_id=saved_session.story_id,
        chapter_id=saved_session.chapter_id,
        words_written=saved_session.words_written,
        duration=saved_session.duration,
        wpm=saved_session.words_per_minute,
        sid=sid,
        extra={"analytics_success": True, "performance_tracking": True}
    )

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
    
    # Check if there's an incomplete session
    session_data = sio.get_session(sid)
    if session_data:
        logger.warning(
            "⚠️ Client disconnected with incomplete session", 
            sid=sid,
            reason=reason,
            session_id=session_data.get('sessionId'),
            user_id=session_data.get('userId'),
            extra={"incomplete_session": True}
        )