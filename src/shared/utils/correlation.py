# Context variables to carry correlation and user info across the request lifecycle
from contextvars import ContextVar
from typing import Optional


_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def set_correlation_id(value: Optional[str]) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> Optional[str]:
    return _correlation_id.get()


def set_user_id(value: Optional[str]) -> None:
    _user_id.set(value)


def get_user_id() -> Optional[str]:
    return _user_id.get()


def clear_context() -> None:
    """Clear context values at the end of a request to avoid leaking between tasks."""
    _correlation_id.set(None)
    _user_id.set(None)