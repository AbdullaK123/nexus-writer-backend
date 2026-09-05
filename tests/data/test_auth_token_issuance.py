import asyncio

import asyncpg

from src.data.repositories.auth_tokens import AuthTokenRepository
from tests.data.factories import make_user


async def test_reissuing_same_purpose_invalidates_previous_token(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)

    first = await repo.create(user_id=user.id, purpose="password_reset")
    second = await repo.create(user_id=user.id, purpose="password_reset")

    assert first != second
    assert await repo.get(token=first, purpose="password_reset") is None
    assert await repo.get(token=second, purpose="password_reset") is not None
    assert await clean_db.fetchval(
        "SELECT COUNT(*) FROM auth_tokens WHERE user_id=$1 AND purpose='password_reset'",
        user.id,
    ) == 1


async def test_different_token_purposes_can_coexist(clean_db: asyncpg.Pool) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)

    verification = await repo.create(user_id=user.id, purpose="email_verification")
    reset = await repo.create(user_id=user.id, purpose="password_reset")

    assert await repo.get(token=verification, purpose="email_verification") is not None
    assert await repo.get(token=reset, purpose="password_reset") is not None
    assert await clean_db.fetchval(
        "SELECT COUNT(*) FROM auth_tokens WHERE user_id=$1", user.id
    ) == 2


async def test_concurrent_reissuance_converges_on_one_active_token(
    clean_db: asyncpg.Pool,
) -> None:
    user = await make_user(clean_db)
    repo = AuthTokenRepository(clean_db)

    issued = await asyncio.gather(
        *(repo.create(user_id=user.id, purpose="password_reset") for _ in range(12))
    )

    rows = await clean_db.fetch(
        "SELECT token_hash FROM auth_tokens WHERE user_id=$1 AND purpose='password_reset'",
        user.id,
    )
    active = [
        token
        for token in issued
        if await repo.get(token=token, purpose="password_reset") is not None
    ]

    assert len(rows) == 1, (
        "concurrent recovery requests must converge on one canonical active credential"
    )
    assert len(active) == 1, (
        "after concurrent issuance, exactly one returned bearer token may remain usable"
    )
