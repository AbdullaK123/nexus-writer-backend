"""Tests for src/service/auth/service.py.

For each function we test the implicit assumptions wrapping the happy path.
Real password hashing is used (bcrypt), real DB rows go through Tortoise/SQLite.
"""
from datetime import datetime, timedelta, timezone

import pytest

from src.data.models import Session, User
from src.data.schemas.auth import (
    AuthCredentials, ConnectionDetails, RegistrationData,
)
from src.infrastructure.auth.password import hash_password
from src.service.auth import service as auth_service
from src.service.exceptions import AuthError, ConflictError, ForbiddenError
from src.shared.utils.correlation import get_user_id, set_user_id
from tests.factories import make_user


# ─── get_user_by_email ───────────────────────────────────────────────────────
class TestGetUserByEmail:
    async def test_returns_none_when_no_user_matches(self):
        assert await auth_service.get_user_by_email("nobody@x.com") is None

    async def test_filters_by_exact_email_not_substring(self):
        await make_user(email="alice@x.com")
        # Substring of an existing email should not match
        assert await auth_service.get_user_by_email("alice") is None


# ─── authenticate_user ───────────────────────────────────────────────────────
class TestAuthenticateUser:
    async def test_raises_auth_error_when_user_not_found(self):
        creds = AuthCredentials(email="ghost@x.com", password="anything")
        with pytest.raises(AuthError, match="Incorrect email or password"):
            await auth_service.authenticate_user(creds)

    async def test_raises_auth_error_when_password_wrong(self):
        # Assumption: verify_password is the gate — wrong password must fail
        await make_user(email="a@x.com", password_hash=hash_password("CorrectP@ss1"))
        creds = AuthCredentials(email="a@x.com", password="WrongP@ss1")
        with pytest.raises(AuthError):
            await auth_service.authenticate_user(creds)

    async def test_does_not_leak_which_field_was_wrong(self):
        # Same error message for "no such user" and "bad password"
        await make_user(email="b@x.com", password_hash=hash_password("CorrectP@ss1"))

        with pytest.raises(AuthError) as e1:
            await auth_service.authenticate_user(
                AuthCredentials(email="b@x.com", password="bad"))
        with pytest.raises(AuthError) as e2:
            await auth_service.authenticate_user(
                AuthCredentials(email="ghost@x.com", password="bad"))

        assert e1.value.message == e2.value.message


# ─── create_session ──────────────────────────────────────────────────────────
class TestCreateSession:
    async def test_persists_session_with_unique_id(self):
        user = await make_user()
        details = ConnectionDetails(ip_address="1.1.1.1", user_agent="ua")

        sid_a = await auth_service.create_session(user.id, details)
        sid_b = await auth_service.create_session(user.id, details)

        # Assumption: generate_session_id produces unique tokens
        assert sid_a != sid_b
        assert await Session.filter(session_id=sid_a).exists()

    async def test_expiry_is_in_the_future_per_config_ttl(self, mocker):
        # Assumption: expires_at = now + config.auth.session_ttl_days
        from src.infrastructure.config import config
        user = await make_user()
        before = datetime.now(timezone.utc)

        sid = await auth_service.create_session(
            user.id, ConnectionDetails())

        session = await Session.get(session_id=sid)
        delta = session.expires_at - before
        assert timedelta(days=config.auth.session_ttl_days) - timedelta(seconds=5) \
            <= delta <= timedelta(days=config.auth.session_ttl_days) + timedelta(seconds=5)

    async def test_records_connection_details(self):
        user = await make_user()
        details = ConnectionDetails(ip_address="9.9.9.9", user_agent="curl")

        sid = await auth_service.create_session(user.id, details)

        session = await Session.get(session_id=sid)
        assert session.ip_address == "9.9.9.9"
        assert session.user_agent == "curl"


# ─── validate_session ────────────────────────────────────────────────────────
class TestValidateSession:
    async def test_raises_when_session_id_falsy(self):
        with pytest.raises(ForbiddenError, match="invalid"):
            await auth_service.validate_session("")

    async def test_raises_when_session_not_found(self):
        with pytest.raises(ForbiddenError, match="expired"):
            await auth_service.validate_session("nonexistent-sid")

    async def test_deletes_and_raises_when_session_expired(self):
        # Assumption: an expired session is purged eagerly to prevent reuse
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await Session.create(session_id="exp", user_id=user.id, expires_at=past)

        with pytest.raises(ForbiddenError, match="expired"):
            await auth_service.validate_session("exp")

        assert not await Session.filter(session_id="exp").exists()

    async def test_raises_when_session_user_no_longer_exists(self, mocker):
        # Assumption: user row still exists when session is validated.
        # We can't easily orphan a Session row (FK cascades on delete), so we
        # patch User.filter to simulate the user being gone at validation time.
        user = await make_user()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await Session.create(session_id="orphan", user_id=user.id, expires_at=future)

        # Force the User lookup inside validate_session to return None
        class _NoUserQS:
            async def first(self):
                return None
        mocker.patch.object(User, "filter", return_value=_NoUserQS())

        with pytest.raises(ForbiddenError, match="does not exist"):
            await auth_service.validate_session("orphan")

    async def test_sets_user_id_in_correlation_context_on_success(self):
        user = await make_user()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await Session.create(session_id="good", user_id=user.id, expires_at=future)
        set_user_id(None)  # reset

        result = await auth_service.validate_session("good")

        assert result.id == user.id
        assert get_user_id() == user.id


# ─── logout_user ─────────────────────────────────────────────────────────────
class TestLogoutUser:
    async def test_silent_when_session_id_falsy(self):
        # Assumption: empty session id → no-op (idempotent logout)
        await auth_service.logout_user("")  # must not raise

    async def test_silent_when_session_already_gone(self):
        # Assumption: re-logout / unknown sid is fine
        await auth_service.logout_user("not-there")

    async def test_deletes_existing_session(self):
        user = await make_user()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await Session.create(session_id="sid", user_id=user.id, expires_at=future)

        await auth_service.logout_user("sid")

        assert not await Session.filter(session_id="sid").exists()


# ─── login_user ──────────────────────────────────────────────────────────────
class TestLoginUser:
    async def test_propagates_authentication_failure(self):
        # Assumption: login is gated by authenticate_user
        with pytest.raises(AuthError):
            await auth_service.login_user(
                AuthCredentials(email="x@x.com", password="bad"),
                ConnectionDetails(),
            )

    async def test_returns_user_response_without_password_hash(self):
        # Assumption: response excludes credentials
        await make_user(email="u@x.com",
                        password_hash=hash_password("RealP@ss1"))

        user_resp, sid = await auth_service.login_user(
            AuthCredentials(email="u@x.com", password="RealP@ss1"),
            ConnectionDetails(),
        )

        assert sid
        assert not hasattr(user_resp, "password_hash")
        assert user_resp.email == "u@x.com"

    async def test_creates_persisted_session_on_success(self):
        await make_user(email="u2@x.com",
                        password_hash=hash_password("RealP@ss1"))

        _, sid = await auth_service.login_user(
            AuthCredentials(email="u2@x.com", password="RealP@ss1"),
            ConnectionDetails(),
        )

        assert await Session.filter(session_id=sid).exists()


# ─── register_user ───────────────────────────────────────────────────────────
class TestRegisterUser:
    async def test_raises_conflict_when_email_already_exists(self):
        # Assumption: email uniqueness checked before insert
        await make_user(email="dup@x.com")

        with pytest.raises(ConflictError):
            await auth_service.register_user(RegistrationData(
                username="x", email="dup@x.com", password="GoodP@ss1"))

    async def test_does_not_create_user_on_conflict(self):
        await make_user(email="dup@x.com")
        before = await User.all().count()

        with pytest.raises(ConflictError):
            await auth_service.register_user(RegistrationData(
                username="x", email="dup@x.com", password="GoodP@ss1"))

        assert await User.all().count() == before

    async def test_password_is_hashed_not_stored_in_plain_text(self):
        # Assumption: plaintext password never lands in password_hash column
        plain = "Plaintxt@1"
        await auth_service.register_user(RegistrationData(
            username="n", email="n@x.com", password=plain))

        user = await User.get(email="n@x.com")
        assert user.password_hash != plain
        assert user.password_hash.startswith("$2")  # bcrypt prefix

    async def test_response_excludes_password_hash(self):
        resp = await auth_service.register_user(RegistrationData(
            username="n", email="r@x.com", password="GoodP@ss1"))

        assert not hasattr(resp, "password_hash")
        assert resp.email == "r@x.com"
