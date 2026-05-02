"""Tests for AuthService with mocked repositories.

We don't go through the DB at all — AuthService depends only on the
UserRepository / SessionRepository protocols, which we mock at the boundary.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from loguru import logger

from src.data.schemas import UserRow, SessionRow
from src.data.schemas.auth import (
    AuthCredentials,
    ConnectionDetails,
    RegistrationData,
)
from src.infrastructure.auth.password import hash_password
from src.service.auth import AuthService
from src.service.exceptions import AuthError, ForbiddenError, ConflictError


# ─── helpers ────────────────────────────────────────────────────────────────


def _make_user(
    *,
    id: str = "user-1",
    username: str = "alice",
    email: str = "alice@example.com",
    password: str = "correct horse battery staple",
    profile_img: str | None = None,
) -> UserRow:
    now = datetime.now(timezone.utc)
    return UserRow(
        id=id,
        username=username,
        email=email,
        password_hash=hash_password(password),
        profile_img=profile_img,
        created_at=now,
        updated_at=now,
    )


def _make_session(
    *,
    session_id: str = "sess-1",
    user_id: str = "user-1",
    expires_in: timedelta = timedelta(days=1),
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> SessionRow:
    now = datetime.now(timezone.utc)
    return SessionRow(
        session_id=session_id,
        user_id=user_id,
        expires_at=now + expires_in,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=now,
        updated_at=now,
    )


def _user_repo() -> MagicMock:
    repo = MagicMock(name="UserRepository")
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


def _session_repo() -> MagicMock:
    repo = MagicMock(name="SessionRepository")
    repo.get = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=True)
    repo.delete_expired = AsyncMock(return_value=0)
    return repo


def _service(user_repo=None, session_repo=None) -> AuthService:
    return AuthService(user_repo or _user_repo(), session_repo or _session_repo())


# ─── authenticate_user ──────────────────────────────────────────────────────


class TestAuthenticateUser:
    async def test_returns_user_on_correct_credentials(self):
        user = _make_user(password="hunter2")
        user_repo = _user_repo()
        user_repo.get_by_email.return_value = user
        svc = _service(user_repo=user_repo)

        result = await svc.authenticate_user(
            AuthCredentials(email=user.email, password="hunter2"),
        )

        assert result is user
        user_repo.get_by_email.assert_awaited_once_with(user.email)

    async def test_unknown_email_raises_auth_error(self):
        svc = _service()

        with pytest.raises(AuthError):
            await svc.authenticate_user(
                AuthCredentials(email="nobody@example.com", password="x"),
            )

    async def test_wrong_password_raises_auth_error(self):
        user = _make_user(password="hunter2")
        user_repo = _user_repo()
        user_repo.get_by_email.return_value = user
        svc = _service(user_repo=user_repo)

        with pytest.raises(AuthError):
            await svc.authenticate_user(
                AuthCredentials(email=user.email, password="wrong"),
            )


# ─── create_session ─────────────────────────────────────────────────────────


class TestCreateSession:
    async def test_persists_session_with_expected_arguments(self):
        session_repo = _session_repo()
        svc = _service(session_repo=session_repo)

        session_id = await svc.create_session(
            user_id="user-1",
            connection_details=ConnectionDetails(
                ip_address="1.2.3.4", user_agent="UA"
            ),
        )

        assert isinstance(session_id, str) and session_id
        session_repo.create.assert_awaited_once()
        kwargs = session_repo.create.call_args.kwargs
        assert kwargs["session_id"] == session_id
        assert kwargs["user_id"] == "user-1"
        assert kwargs["ip_address"] == "1.2.3.4"
        assert kwargs["user_agent"] == "UA"
        assert kwargs["expires_at"] > datetime.now(timezone.utc)


# ─── validate_session ───────────────────────────────────────────────────────


class TestValidateSession:
    async def test_returns_user_for_valid_session(self):
        user = _make_user()
        session = _make_session(user_id=user.id)
        user_repo = _user_repo()
        session_repo = _session_repo()
        session_repo.get.return_value = session
        user_repo.get_by_id.return_value = user
        svc = _service(user_repo=user_repo, session_repo=session_repo)

        result = await svc.validate_session(session.session_id)

        assert result is user
        session_repo.get.assert_awaited_once_with(session.session_id)
        user_repo.get_by_id.assert_awaited_once_with(user.id)

    async def test_missing_session_id_raises_forbidden(self):
        with pytest.raises(ForbiddenError):
            await _service().validate_session("")

    async def test_unknown_session_raises_forbidden(self):
        with pytest.raises(ForbiddenError):
            await _service().validate_session("missing")

    async def test_expired_session_is_deleted_and_raises_forbidden(self):
        session = _make_session(expires_in=timedelta(seconds=-1))
        session_repo = _session_repo()
        session_repo.get.return_value = session
        svc = _service(session_repo=session_repo)

        with pytest.raises(ForbiddenError):
            await svc.validate_session(session.session_id)
        session_repo.delete.assert_awaited_once_with(session.session_id)

    async def test_orphaned_session_raises_forbidden(self):
        session = _make_session()
        session_repo = _session_repo()
        session_repo.get.return_value = session
        user_repo = _user_repo()
        user_repo.get_by_id.return_value = None
        svc = _service(user_repo=user_repo, session_repo=session_repo)

        with pytest.raises(ForbiddenError):
            await svc.validate_session(session.session_id)


# ─── logout_user ────────────────────────────────────────────────────────────


class TestLogoutUser:
    async def test_no_op_for_empty_session_id(self):
        session_repo = _session_repo()
        svc = _service(session_repo=session_repo)

        await svc.logout_user("")

        session_repo.delete.assert_not_awaited()

    async def test_deletes_session_when_present(self):
        session_repo = _session_repo()
        session_repo.delete.return_value = True
        svc = _service(session_repo=session_repo)

        await svc.logout_user("sess-1")

        session_repo.delete.assert_awaited_once_with("sess-1")

    async def test_swallows_unknown_session(self):
        session_repo = _session_repo()
        session_repo.delete.return_value = False
        svc = _service(session_repo=session_repo)

        await svc.logout_user("ghost")  # no raise


# ─── login_user ─────────────────────────────────────────────────────────────


class TestLoginUser:
    async def test_returns_user_response_and_session_id(self):
        user = _make_user(password="hunter2")
        user_repo = _user_repo()
        user_repo.get_by_email.return_value = user
        session_repo = _session_repo()
        svc = _service(user_repo=user_repo, session_repo=session_repo)

        response, session_id = await svc.login_user(
            AuthCredentials(email=user.email, password="hunter2"),
            ConnectionDetails(ip_address=None, user_agent=None),
        )

        assert response.email == user.email
        assert response.username == user.username
        assert isinstance(session_id, str) and session_id
        session_repo.create.assert_awaited_once()


# ─── register_user ──────────────────────────────────────────────────────────


class TestRegisterUser:
    async def test_creates_user_when_email_is_free(self):
        user_repo = _user_repo()
        created = _make_user(email="new@example.com", username="new")
        user_repo.create.return_value = created
        svc = _service(user_repo=user_repo)

        result = await svc.register_user(
            RegistrationData(
                username="new",
                email="new@example.com",
                password="Hunter2!hunter",
                profile_img=None,
            ),
        )

        assert result.email == "new@example.com"
        user_repo.get_by_email.assert_awaited_once_with("new@example.com")
        user_repo.create.assert_awaited_once()
        kwargs = user_repo.create.call_args.kwargs
        assert kwargs["username"] == "new"
        assert kwargs["email"] == "new@example.com"
        assert kwargs["password_hash"] != "Hunter2!hunter"  # hashed

    async def test_duplicate_email_raises_conflict(self):
        user_repo = _user_repo()
        user_repo.get_by_email.return_value = _make_user()
        svc = _service(user_repo=user_repo)

        with pytest.raises(ConflictError):
            await svc.register_user(
                RegistrationData(
                    username="someone",
                    email="alice@example.com",
                    password="Hunter2!hunter",
                    profile_img=None,
                ),
            )
        user_repo.create.assert_not_awaited()


# ─── cleanup_expired_sessions ───────────────────────────────────────────────


class TestCleanupExpiredSessions:
    async def test_no_op_when_nothing_deleted(self, mocker):
        spy = mocker.spy(logger, "info")
        session_repo = _session_repo()
        session_repo.delete_expired.return_value = 0
        svc = _service(session_repo=session_repo)

        await svc.cleanup_expired_sessions()

        session_repo.delete_expired.assert_awaited_once()
        assert not any(
            "session.cleanup_complete" in str(c) for c in spy.call_args_list
        )

    async def test_logs_completion_when_anything_deleted(self, mocker):
        spy = mocker.spy(logger, "info")
        session_repo = _session_repo()
        session_repo.delete_expired.return_value = 7
        svc = _service(session_repo=session_repo)

        await svc.cleanup_expired_sessions()

        assert any(
            "session.cleanup_complete" in str(c.args) for c in spy.call_args_list
        )
