from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message
from loguru import logger
import time
import uuid
from typing import Callable
from app.utils.logging_context import (
    set_correlation_id,
    set_user_id,
    clear_context,
    context_logger,
)


SENSITIVE_PATHS = {"/auth/login", "/auth/register"}
SENSITIVE_FIELDS = {"password", "password_hash"}


def _redact_query_string(qs: str) -> str:
    # very light redaction for query parameters containing sensitive keys
    if not qs:
        return qs
    parts = qs.split("&")
    redacted = []
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            if k.lower() in SENSITIVE_FIELDS:
                redacted.append(f"{k}=<redacted>")
            else:
                redacted.append(p)
        else:
            redacted.append(p)
    return "&".join(redacted)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each HTTP request/response with structured fields.

    Notes:
    - Avoids reading request/response bodies to prevent consumption/overhead.
    - Redacts obvious secrets in query string and avoids logging bodies for sensitive paths.
    - If get_current_user sets request.state.user_id, it will be included.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start = time.perf_counter()
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Client info
        client_ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else None)
        user_agent = request.headers.get("User-Agent")
        session_id = request.cookies.get("session_id")
        path = request.url.path
        method = request.method
        query = _redact_query_string(request.url.query)

        # Set correlation and user context for downstream logs
        set_correlation_id(correlation_id)
        # user id may be set later by deps; initialize if present now
        set_user_id(getattr(request.state, "user_id", None))

        # Pre log (minimal)
        context_logger(http=True).info(
            "HTTP {method} {path} started",
            method=method,
            path=path,
        )

        # Wrap response to capture content length
        response: Response
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            context_logger(http=True).exception(
                "HTTP {method} {path} failed in {duration_ms:.2f} ms",
                method=method,
                path=path,
                duration_ms=duration_ms,
            )
            raise

        # Pull possible user id placed by dependencies
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            set_user_id(user_id)

        # Try to get response content length from header/body
        resp_len = None
        try:
            if response.headers.get("content-length"):
                resp_len = int(response.headers["content-length"])  # noqa: SLF001
        except Exception:
            resp_len = None

        duration_ms = (time.perf_counter() - start) * 1000

        # Structured final log
        extra = {
            "http": True,
            "correlation_id": correlation_id,
            "method": method,
            "path": path,
            "query": query,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "session_present": bool(session_id),
            "user_id": user_id,
            "response_length": resp_len,
        }

        # Avoid logging bodies; add hint for sensitive paths
        if path in SENSITIVE_PATHS:
            extra["note"] = "sensitive_path"

        context_logger(**extra).info(
            "{method} {path} -> {status} in {duration_ms} ms",
            method=method,
            path=path,
            status=status,
            duration_ms=round(duration_ms, 2),
        )

        # Ensure correlation id is visible to clients
        response.headers.setdefault("X-Request-ID", correlation_id)
        # Always clear context at the end of the request
        clear_context()
        return response
