import pytest
from starlette.requests import Request

from src.app.dependencies.auth import get_current_user
from src.service.exceptions import AuthError, ForbiddenError


class StaleSessionAuthService:
    async def validate_session(self, session_id: str):
        assert session_id == "stale-session"
        raise ForbiddenError("Your session has expired. Please log in again.")


def make_request() -> Request:
    return Request({"type": "http", "headers": []})


async def test_missing_cookie_is_unauthorized() -> None:
    with pytest.raises(AuthError) as exc_info:
        await get_current_user(make_request(), None, StaleSessionAuthService())

    assert exc_info.value.status_code == 401


async def test_stale_session_is_normalized_to_unauthorized() -> None:
    with pytest.raises(AuthError) as exc_info:
        await get_current_user(
            make_request(),
            "stale-session",
            StaleSessionAuthService(),
        )

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.message
