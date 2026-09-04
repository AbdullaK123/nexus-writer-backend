from datetime import datetime, timedelta, timezone

import asyncpg
import pytest

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import AuthCredentials, ConnectionDetails
from src.infrastructure.auth.password import hash_password, verify_password
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError


OLD_PASSWORD = "OldStrong1!Password"
NEW_PASSWORD = "NewStrong2!Password"


class FailingDeleteAllSessionRepository(SessionRepository):
    async def delete_all(self, user_id: str, executor=None) -> bool:
        raise RuntimeError("injected session revocation failure")


async def make_password_user(pool: asyncpg.Pool, *, email: str):
    return await UserRepository(pool).create(
        username=email.split("@")[0],
        email=email,
        password_hash=hash_password(OLD_PASSWORD),
        profile_img=None,
        verified=True,
    )


def build_service(
    pool: asyncpg.Pool,
    *,
    session_repo: SessionRepository | None = None,
    token_repo: AuthTokenRepository | None = None,
) -> AuthService:
    return AuthService(
        UserRepository(pool),
        session_repo or SessionRepository(pool),
        token_repo or AuthTokenRepository(pool),
        None,  # type: ignore[arg-type]
    )


async def create_session(repo: SessionRepository, user_id: str, session_id: str) -> None:
    await repo.create(
        session_id=session_id,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )


async def test_valid_password_reset_changes_credential_consumes_token_and_revokes_only_user_sessions(
    clean_db: asyncpg.Pool,
) -> None:
    target = await make_password_user(clean_db, email="reset-target@example.com")
    other = await make_password_user(clean_db, email="reset-other@example.com")
    session_repo = SessionRepository(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, session_repo=session_repo, token_repo=token_repo)

    await create_session(session_repo, target.id, "target-session-1")
    await create_session(session_repo, target.id, "target-session-2")
    await create_session(session_repo, other.id, "other-session")
    token = await token_repo.create(user_id=target.id, purpose="password_reset")

    await service.reset_password(token, NEW_PASSWORD)

    with pytest.raises(AuthError):
        await service.authenticate_user(
            AuthCredentials(email=target.email, password=OLD_PASSWORD)
        )
    authenticated = await service.authenticate_user(
        AuthCredentials(email=target.email, password=NEW_PASSWORD)
    )
    assert authenticated.id == target.id

    assert await token_repo.get(token=token, purpose="password_reset") is None
    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM "session" WHERE user_id=$1', target.id
    ) == 0
    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM "session" WHERE user_id=$1', other.id
    ) == 1


async def test_expired_password_reset_token_leaves_password_and_sessions_untouched(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_password_user(clean_db, email="expired-reset@example.com")
    session_repo = SessionRepository(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, session_repo=session_repo, token_repo=token_repo)
    await create_session(session_repo, user.id, "still-valid-session")
    token = await token_repo.create(user_id=user.id, purpose="password_reset")
    await clean_db.execute(
        "UPDATE auth_tokens SET expires_at=$1 WHERE user_id=$2 AND purpose='password_reset'",
        datetime.now(timezone.utc) - timedelta(seconds=1),
        user.id,
    )

    with pytest.raises(AuthError, match="expired"):
        await service.reset_password(token, NEW_PASSWORD)

    password_hash = await clean_db.fetchval(
        'SELECT password_hash FROM "user" WHERE id=$1', user.id
    )
    assert verify_password(OLD_PASSWORD, password_hash)
    assert await session_repo.get("still-valid-session") is not None
    assert await token_repo.get(token=token, purpose="password_reset") is None


async def test_invalid_password_reset_token_changes_nothing(clean_db: asyncpg.Pool) -> None:
    user = await make_password_user(clean_db, email="invalid-reset@example.com")
    session_repo = SessionRepository(clean_db)
    service = build_service(clean_db, session_repo=session_repo)
    await create_session(session_repo, user.id, "session-before-invalid-reset")

    with pytest.raises(AuthError, match="Invalid"):
        await service.reset_password("garbage-reset-token", NEW_PASSWORD)

    password_hash = await clean_db.fetchval(
        'SELECT password_hash FROM "user" WHERE id=$1', user.id
    )
    assert verify_password(OLD_PASSWORD, password_hash)
    assert await session_repo.get("session-before-invalid-reset") is not None


async def test_verification_token_cannot_reset_password(clean_db: asyncpg.Pool) -> None:
    user = await make_password_user(clean_db, email="wrong-purpose-reset@example.com")
    session_repo = SessionRepository(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, session_repo=session_repo, token_repo=token_repo)
    await create_session(session_repo, user.id, "wrong-purpose-session")
    token = await token_repo.create(user_id=user.id, purpose="email_verification")

    with pytest.raises(AuthError, match="Invalid"):
        await service.reset_password(token, NEW_PASSWORD)

    password_hash = await clean_db.fetchval(
        'SELECT password_hash FROM "user" WHERE id=$1', user.id
    )
    assert verify_password(OLD_PASSWORD, password_hash)
    assert await session_repo.get("wrong-purpose-session") is not None
    assert await token_repo.get(token=token, purpose="email_verification") is not None


async def test_oauth_only_user_can_set_local_password_via_verified_email_reset(
    clean_db: asyncpg.Pool,
) -> None:
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, token_repo=token_repo)
    account = await service.get_or_create_oauth_account(
        provider="google",
        provider_user_id="oauth-reset-sub",
        email="oauth-reset@example.com",
        name="OAuth Reset User",
    )
    token = await token_repo.create(user_id=account.user_id, purpose="password_reset")

    await service.reset_password(token, NEW_PASSWORD)

    authenticated = await service.authenticate_user(
        AuthCredentials(email="oauth-reset@example.com", password=NEW_PASSWORD)
    )
    assert authenticated.id == account.user_id


async def test_password_token_and_session_revocation_roll_back_together_on_failure(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_password_user(clean_db, email="rollback-reset@example.com")
    normal_session_repo = SessionRepository(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    await create_session(normal_session_repo, user.id, "rollback-session")
    token = await token_repo.create(user_id=user.id, purpose="password_reset")
    service = build_service(
        clean_db,
        session_repo=FailingDeleteAllSessionRepository(clean_db),
        token_repo=token_repo,
    )

    with pytest.raises(RuntimeError, match="injected session revocation failure"):
        await service.reset_password(token, NEW_PASSWORD)

    password_hash = await clean_db.fetchval(
        'SELECT password_hash FROM "user" WHERE id=$1', user.id
    )
    assert verify_password(OLD_PASSWORD, password_hash), (
        "password mutation must roll back if session revocation cannot complete"
    )
    assert await token_repo.get(token=token, purpose="password_reset") is not None
    assert await normal_session_repo.get("rollback-session") is not None
