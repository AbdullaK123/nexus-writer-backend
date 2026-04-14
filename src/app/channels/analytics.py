from socketio.async_server import AsyncServer
from src.service.analytics.service import AnalyticsService
from src.service.analytics.session_cache import SessionCacheService
from src.data.schemas.analytics import WritingSession, WritingSessionEvent
from src.shared.utils.decorators import log_errors
from dependency_injector.wiring import inject, Provide
from src.app.di.containers import ApplicationContainer
from src.infrastructure.config import settings
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
import asyncio

log = get_layer_logger(LAYER_APP)


sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins,
    logger=True,
    engineio_logger=True
)

@sio.on('session_start', namespace='/analytics')
@log_errors
@inject
def handle_session_start(
    sid: str,
    session_start_data: dict,
    session_cache: SessionCacheService = Provide[ApplicationContainer.session_cache_service],
):
    log.info(
        "Writing session start event received", 
        sid=sid, 
        extra={"event_type": "session_start"}
    )
    
    # Validate incoming data
    event = WritingSessionEvent(**session_start_data)
    
    log.debug(
        "Session data validated successfully", 
        session_id=event.sessionId,
        user_id=event.userId,
        story_id=event.storyId, 
        chapter_id=event.chapterId,
        initial_word_count=event.wordCount,
        sid=sid
    )
    
    session_cache.save(sid, event.model_dump())
    
    log.success(
        "Writing session started and stored", 
        session_id=event.sessionId,
        user_id=event.userId,
        sid=sid,
        extra={"performance_tracking": True}
    )

@sio.on('session_end', namespace='/analytics')
@log_errors 
@inject
def handle_session_end(
    sid: str,
    session_end_data: dict,
    session_cache: SessionCacheService = Provide[ApplicationContainer.session_cache_service],
):
    log.info(
        "Writing session end event received", 
        sid=sid,
        extra={"event_type": "session_end"}
    )
    
    # Validate end data
    end_event = WritingSessionEvent(**session_end_data)
    
    log.debug(
        "End event data validated", 
        session_id=end_event.sessionId,
        final_word_count=end_event.wordCount,
        sid=sid
    )
    
    start_data = session_cache.get(sid)
    
    if not start_data:
        log.warning(
            "No session start data found", 
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
    
    log.debug(
        "Session metrics calculated", 
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
    
    log.info(
        "Saving writing session to DuckDB", 
        session_id=session.id,
        user_id=session.user_id,
        words_written=words_written,
        duration_minutes=round(duration_minutes, 2),
        sid=sid,
        extra={"db_operation": True}
    )
    
    loop = asyncio.get_event_loop()
    task = loop.create_task(save_to_duckdb_async(session, sid))
    task.add_done_callback(lambda t: handle_task_completion(t, session.id, sid))
    
    session_cache.delete(sid)

@log_errors
def handle_task_completion(task, session_id: str, sid: str):
    if task.exception() is None:
        log.success(
            "Writing session successfully saved to DuckDB", 
            session_id=session_id,
            sid=sid,
            extra={"analytics_success": True, "performance_tracking": True}
        )
    else:
        exception = task.exception()
        log.error(
            "Failed to save session to DuckDB",
            session_id=session_id,
            error_type=type(exception).__name__,
            error_message=str(exception),
            sid=sid,
            extra={"analytics_failure": True}
        )

@log_errors
@inject
async def save_to_duckdb_async(
    session: WritingSession,
    sid: str,
    analytics: AnalyticsService = Provide[ApplicationContainer.analytics_service],
):
    saved_session = await analytics.write_session(session)
    return saved_session

@sio.on('connect', namespace='/analytics')
@log_errors
def on_connect(sid, environ, auth=None):
    log.info(
        "Client connected to analytics namespace", 
        sid=sid,
        user_agent=environ.get('HTTP_USER_AGENT', 'unknown'),
        origin=environ.get('HTTP_ORIGIN', 'unknown'),
        auth=auth,
        extra={"connection_event": True}
    )

@sio.on('disconnect', namespace='/analytics')
@log_errors
@inject
def on_disconnect(
    sid,
    reason,
    session_cache: SessionCacheService = Provide[ApplicationContainer.session_cache_service],
):
    log.info(
        "Client disconnected from analytics namespace", 
        sid=sid,
        reason=reason,
        extra={"connection_event": True}
    )
    session_data = session_cache.get(sid)
    if session_data:
        log.warning(
            "Client disconnected with incomplete session - cleaning up", 
            sid=sid,
            reason=reason,
            session_id=session_data.get('sessionId'),
            user_id=session_data.get('userId'),
            extra={"incomplete_session": True}
        )
        session_cache.delete(sid)