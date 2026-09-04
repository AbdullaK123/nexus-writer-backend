import hashlib
from datetime import datetime, timedelta, timezone

import asyncpg
import pytest
from uuid_extensions import uuid7str

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.user import UserRepository
from src.infrastructure.config import config
from tests.data.factories import make_user


async def test_auth_token_create_hashes_secret_and_sets_bounded_ttl(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)

    before = datetime.now(timezone.utc)
    token = await repo.create(user_id=user.id, purpose="password_reset")
    after = datetime.now(timezone.utc)

    row = await clean_db.fetchrow(
        'SELECT token_hash, purpose, expires_at FROM auth_tokens WHERE user_id=$1',
        user.id,
    )
    assert row is not None
    assert row["token_hash"] != token, "raw bearer tokens must never be stored in PostgreSQL"
    assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert row["purpose"] == "password_reset"

    minimum = before + timedelta(minutes=config.auth.auth_token_ttl_mins)
    maximum = after + timedelta(minutes=config.auth.auth_token_ttl_mins)
    assert minimum <= row["expires_at"] <= maximum


async def test_auth_token_get_is_scoped_by_purpose(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)
    token = await repo.create(user_id=user.id, purpose="email_verification")

    assert await repo.get(token=token, purpose="email_verification") is not None
    assert await repo.get(token=token, purpose="password_reset") is None, (
        "a verification token must never become a password-reset credential"
    )


async def test_auth_token_delete_requires_exact_user_token_and_purpose(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    other = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)
    token = await repo.create(user_id=user.id, purpose="password_reset")

    await repo.delete(user_id=other.id, token=token, purpose="password_reset")
    assert await repo.get(token=token, purpose="password_reset") is not None

    await repo.delete(user_id=user.id, token=token, purpose="email_verification")
    assert await repo.get(token=token, purpose="password_reset") is not None

    await repo.delete(user_id=user.id, token=token, purpose="password_reset")
    assert await repo.get(token=token, purpose="password_reset") is None


async def test_auth_tokens_cascade_when_user_is_deleted(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)
    await repo.create(user_id=user.id, purpose="email_verification")
    await repo.create(user_id=user.id, purpose="password_reset")

    await clean_db.execute('DELETE FROM "user" WHERE id=$1', user.id)

    remaining = await clean_db.fetchval(
        'SELECT COUNT(*) FROM auth_tokens WHERE user_id=$1', user.id
    )
    assert remaining == 0


async def test_database_rejects_unknown_auth_token_purpose(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)

    with pytest.raises(asyncpg.CheckViolationError):
        await clean_db.execute(
            """
            INSERT INTO auth_tokens (id, user_id, token_hash, purpose, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid7str(),
            user.id,
            "invalid-purpose-hash",
            "not_a_real_purpose",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )


async def test_verify_user_updates_only_target_user(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    other = await make_user(clean_db)
    repo = UserRepository(clean_db)

    await repo.verify_user(user.id)

    target_verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    )
    other_verified = await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', other.id
    )

    assert target_verified is True
    assert other_verified is False
