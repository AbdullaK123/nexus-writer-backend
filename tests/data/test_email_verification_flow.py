from datetime import datetime, timedelta, timezone

import asyncpg
import pytest

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import RegistrationData
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError
from tests.data.factories import make_user


class FailingDeleteAuthTokenRepository(AuthTokenRepository):
    async def delete(self, **kwargs) -> None:
        raise RuntimeError("injected token delete failure")


def build_service(pool: asyncpg.Pool, token_repo: AuthTokenRepository | None = None) -> AuthService:
    return AuthService(
        UserRepository(pool),
        SessionRepository(pool),
        token_repo or AuthTokenRepository(pool),
        None,  # type: ignore[arg-type]
    )


async def test_password_registration_starts_unverified_and_issues_verification_token(
    clean_db: asyncpg.Pool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_send(payload: dict) -> dict:
        return {"id": "email-1"}

    monkeypatch.setattr("src.service.auth.service.resend.Emails.send_async", fake_send)
    service = build_service(clean_db)

    user = await service.register_user(
        RegistrationData(
            username="verify-me",
            email="verify-me@example.com",
            password="Strong1!Password",
        )
    )

    row = await clean_db.fetchrow(
        'SELECT email_verified FROM "user" WHERE id=$1',
        user.id,
    )
    token_count = await clean_db.fetchval(
        "SELECT COUNT(*) FROM auth_tokens WHERE user_id=$1 AND purpose='email_verification'",
        user.id,
    )

    assert row is not None and row["email_verified"] is False
    assert token_count == 1


async def test_oauth_created_user_starts_verified(clean_db: asyncpg.Pool) -> None:
    service = build_service(clean_db)

    account = await service.get_or_create_oauth_account(
        provider="google",
        provider_user_id="verified-google-sub",
        email="oauth-verified@example.com",
        name="Verified OAuth User",
    )

    verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1',
        account.user_id,
    )
    assert verified is True


async def test_valid_verification_token_verifies_exact_user_and_is_consumed(
    clean_db: asyncpg.Pool,
) -> None:
    target = await make_user(clean_db)
    other = await make_user(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, token_repo)
    token = await token_repo.create(user_id=target.id, purpose="email_verification")

    await service.verify_email(token)

    target_verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', target.id
    )
    other_verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', other.id
    )
    remaining = await token_repo.get(token=token, purpose="email_verification")

    assert target_verified is True
    assert other_verified is False
    assert remaining is None


async def test_expired_verification_token_is_deleted_without_verifying_user(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, token_repo)
    token = await token_repo.create(user_id=user.id, purpose="email_verification")
    await clean_db.execute(
        "UPDATE auth_tokens SET expires_at=$1 WHERE user_id=$2 AND purpose='email_verification'",
        datetime.now(timezone.utc) - timedelta(seconds=1),
        user.id,
    )

    with pytest.raises(AuthError, match="expired"):
        await service.verify_email(token)

    verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    )
    assert verified is False
    assert await token_repo.get(token=token, purpose="email_verification") is None


async def test_garbage_verification_token_changes_nothing(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    service = build_service(clean_db)

    with pytest.raises(AuthError, match="Invalid"):
        await service.verify_email("definitely-not-a-token")

    verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    )
    assert verified is False


async def test_password_reset_token_cannot_verify_email(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, token_repo)
    token = await token_repo.create(user_id=user.id, purpose="password_reset")

    with pytest.raises(AuthError, match="Invalid"):
        await service.verify_email(token)

    verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    )
    assert verified is False
    assert await token_repo.get(token=token, purpose="password_reset") is not None


async def test_successful_verification_token_cannot_be_replayed(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    token_repo = AuthTokenRepository(clean_db)
    service = build_service(clean_db, token_repo)
    token = await token_repo.create(user_id=user.id, purpose="email_verification")

    await service.verify_email(token)

    with pytest.raises(AuthError, match="Invalid"):
        await service.verify_email(token)


async def test_verification_and_token_consumption_roll_back_together_on_failure(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    normal_repo = AuthTokenRepository(clean_db)
    token = await normal_repo.create(user_id=user.id, purpose="email_verification")
    service = build_service(clean_db, FailingDeleteAuthTokenRepository(clean_db))

    with pytest.raises(RuntimeError, match="injected token delete failure"):
        await service.verify_email(token)

    verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    )
    assert verified is False, (
        "verification and token consumption must be one transaction; a failure after "
        "the user update must roll the verification back"
    )
    assert await normal_repo.get(token=token, purpose="email_verification") is not None
