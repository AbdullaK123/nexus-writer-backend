from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Request, Response

import src.app.controllers.auth as auth_controller
from src.data.schemas.auth import AuthCredentials


class FakeAuthService:
    def __init__(self) -> None:
        self.logged_out: list[str] = []

    async def login_user(self, credentials, connection_details):
        return object(), "session-secret"

    async def logout_user(self, session_id: str) -> None:
        self.logged_out.append(session_id)


def request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/login",
            "headers": [
                (b"x-real-ip", b"203.0.113.5"),
                (b"user-agent", b"pytest"),
            ],
        }
    )


@pytest.mark.asyncio
async def test_login_cookie_preserves_security_attributes_in_production(monkeypatch) -> None:
    monkeypatch.setattr(auth_controller, "settings", SimpleNamespace(env="prod"))
    monkeypatch.setattr(
        auth_controller,
        "app_config",
        SimpleNamespace(auth=SimpleNamespace(cookie_max_age_seconds=3600)),
    )
    response = Response()
    credentials = AuthCredentials.model_construct(
        email="writer@example.com",
        password="irrelevant-to-controller-test",
    )

    await auth_controller.login_user(
        request(),
        response,
        credentials,
        auth_service=FakeAuthService(),
    )

    cookie = response.headers.get("set-cookie", "")
    lowered = cookie.lower()
    assert "session_id=session-secret" in cookie
    assert "httponly" in lowered, (
        "the session cookie must remain unreadable to browser JavaScript; losing HttpOnly turns any XSS into session theft"
    )
    assert "samesite=lax" in lowered
    assert "secure" in lowered, (
        "production sessions must never be sent over plaintext HTTP"
    )
    assert "max-age=3600" in lowered


@pytest.mark.asyncio
async def test_logout_expires_the_session_cookie() -> None:
    response = Response()
    service = FakeAuthService()

    await auth_controller.logout_user(
        request(),
        response,
        user=object(),
        session_id="session-secret",
        auth_service=service,
    )

    cookie = response.headers.get("set-cookie", "").lower()
    assert service.logged_out == ["session-secret"]
    assert "session_id=" in cookie
    assert "max-age=0" in cookie, (
        "logout must expire the browser cookie as well as revoke server state or stale credentials can survive on shared machines"
    )
