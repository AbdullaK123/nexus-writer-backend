from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.controllers.auth import user_controller
from app.controllers.chapter import chapter_controller
from app.controllers.story import story_controller
from app.controllers.jobs import job_controller
from app.config.logging import setup_logging
from app.channels.analytics import sio
from socketio.asgi import ASGIApp  # type: ignore
from app.config.lifespan import lifespan
from app.middleware.http_logging import HTTPLoggingMiddleware
from loguru import logger
from app.utils.logging_context import get_correlation_id
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global exception handler to ensure bullet-proof logging with correlation id
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception while processing request")
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