from typing import Any

import pytest

from src.data.schemas.auth import ConnectionDetails, UserResponse
from src.service.auth.service import AuthService


class RecordingLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.events.append((message, args, kwargs))

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.events.append((message, args, kwargs))


def assert_secret_absent(logger: RecordingLogger, secret: str) -> None:
    rendered = repr(logger.events)
    assert secret not in rendered, (
        "session IDs are bearer credentials; emitting one into logs turns every log sink, "
        "trace exporter, and support bundle into a session-hijacking surface"
    )


async def test_session_creation_never_logs_raw_session_id(
    auth_service: AuthService,
    test_user: UserResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "super-secret-session-token"
    logger = RecordingLogger()
    monkeypatch.setattr("src.service.auth.service.logger", logger)
    monkeypatch.setattr("src.service.auth.service.generate_session_id", lambda: secret)

    created = await auth_service.create_session(
        test_user.id,
        ConnectionDetails(ip_address="127.0.0.1", user_agent="pytest"),
    )

    assert created == secret
    assert_secret_absent(logger, secret)


async def test_logout_never_logs_raw_session_id(
    auth_service: AuthService,
    test_user: UserResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "logout-secret-session-token"
    logger = RecordingLogger()
    monkeypatch.setattr("src.service.auth.service.logger", logger)
    monkeypatch.setattr("src.service.auth.service.generate_session_id", lambda: secret)

    await auth_service.create_session(
        test_user.id,
        ConnectionDetails(ip_address="127.0.0.1", user_agent="pytest"),
    )
    logger.events.clear()

    await auth_service.logout_user(secret)

    assert_secret_absent(logger, secret)
