from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.app.controllers.auth import user_controller
from src.app.controllers.chapter import chapter_controller
from src.app.controllers.story import story_controller
from src.app.controllers.jobs import job_controller
from src.infrastructure.config.logging import setup_logging
from src.app.channels.analytics import sio
from socketio.asgi import ASGIApp  # type: ignore
from src.app.lifespan import lifespan
from src.app.middleware.http_logging import HTTPLoggingMiddleware
from src.shared.utils.logging_context import get_correlation_id, context_logger
from src.service.exceptions import ServiceError
from src.data.exceptions import DataError, NotFoundError as DataNotFound, DuplicateError, DataIntegrityError
from src.infrastructure.exceptions import InfrastructureError
from src.infrastructure.config import settings
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(
    title="Nexus Writer API",
    description="The backend API for Nexus Writer",
    version="1.0",
    lifespan=lifespan
)

setup_logging()

# HTTP logging middleware should wrap as wide as possible
app.add_middleware(HTTPLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# ── Layer exception handlers ──────────────────────────────────────────

@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    cid = get_correlation_id()
    detail = {"code": exc.code, "message": exc.message, "correlation_id": cid}
    if hasattr(exc, "fields") and exc.fields:
        detail["fields"] = exc.fields
    context_logger().warning("Service error: {code} — {message}", code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    cid = get_correlation_id()
    if isinstance(exc, DataNotFound):
        return JSONResponse(
            status_code=404,
            content={"detail": {"code": "NOT_FOUND", "message": str(exc), "correlation_id": cid}},
        )
    if isinstance(exc, DuplicateError):
        return JSONResponse(
            status_code=409,
            content={"detail": {"code": "CONFLICT", "message": str(exc), "correlation_id": cid}},
        )
    if isinstance(exc, DataIntegrityError):
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": "DATA_INTEGRITY", "message": str(exc), "correlation_id": cid}},
        )
    context_logger().error("Unhandled data error: {exc}", exc=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "DATA_ERROR", "message": "A data error occurred", "correlation_id": cid}},
    )


@app.exception_handler(InfrastructureError)
async def infrastructure_error_handler(request: Request, exc: InfrastructureError):
    cid = get_correlation_id()
    context_logger().error("Infrastructure error: {exc}", exc=exc)
    return JSONResponse(
        status_code=503,
        content={"detail": {"code": "SERVICE_UNAVAILABLE", "message": "A dependent service is temporarily unavailable", "correlation_id": cid}},
    )


# Global exception handler to ensure bullet-proof logging with correlation id
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    context_logger().exception("Unhandled exception while processing request")
    cid = get_correlation_id()
    payload = {"detail": "Internal Server Error", "correlation_id": cid}
    return JSONResponse(status_code=500, content=payload)

app.include_router(user_controller)
app.include_router(chapter_controller)
app.include_router(story_controller)
app.include_router(job_controller)

@app.get('/health')
async def get_health() -> dict:
    return {
        'message': 'Everything is healthy!'
    }

socket_app = ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host='0.0.0.0', port=8000)