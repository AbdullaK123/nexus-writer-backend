import asyncio

import asyncpg

from src.data.repositories.user import UserRepository
from src.service.auth.service import AuthService


async def test_concurrent_first_oauth_callbacks_create_one_canonical_account(
    clean_db: asyncpg.Pool,
) -> None:
    service = AuthService(
        UserRepository(clean_db),
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
    )

    async def login():
        return await service.get_or_create_oauth_account(
            provider="google",
            provider_user_id="google-sub-race",
            email="oauth-race@example.com",
            name="OAuth Race User",
            email_verified=True,
        )

    results = await asyncio.gather(*(login() for _ in range(8)))

    assert len({result.id for result in results}) == 1, (
        "concurrent callbacks for one provider identity must converge on one OAuth "
        "account instead of exposing duplicate-key races to callers"
    )
    assert len({result.user_id for result in results}) == 1, (
        "concurrent first login must create exactly one canonical Nexus user"
    )

    user_count = await clean_db.fetchval(
        'SELECT COUNT(*) FROM "user" WHERE email=$1',
        "oauth-race@example.com",
    )
    account_count = await clean_db.fetchval(
        """
        SELECT COUNT(*)
        FROM oauth_accounts
        WHERE provider=$1 AND provider_user_id=$2
        """,
        "google",
        "google-sub-race",
    )

    assert user_count == 1
    assert account_count == 1


async def test_concurrent_oauth_identities_for_same_email_link_to_one_user(
    clean_db: asyncpg.Pool,
) -> None:
    service = AuthService(
        UserRepository(clean_db),
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
    )

    first, second = await asyncio.gather(
        service.get_or_create_oauth_account(
            provider="google",
            provider_user_id="google-sub-one",
            email="shared-oauth@example.com",
            name="Shared OAuth User",
            email_verified=True,
        ),
        service.get_or_create_oauth_account(
            provider="github",
            provider_user_id="github-sub-two",
            email="shared-oauth@example.com",
            name="Shared OAuth User",
            email_verified=True,
        ),
    )

    assert first.user_id == second.user_id, (
        "different OAuth identities asserting the same canonical email concurrently "
        "must link to one Nexus user rather than racing to create duplicate users"
    )

    user_count = await clean_db.fetchval(
        'SELECT COUNT(*) FROM "user" WHERE email=$1',
        "shared-oauth@example.com",
    )
    linked_accounts = await clean_db.fetchval(
        "SELECT COUNT(*) FROM oauth_accounts WHERE user_id=$1",
        first.user_id,
    )

    assert user_count == 1
    assert linked_accounts == 2


async def test_concurrent_equivalent_emails_use_one_canonical_user(
    clean_db: asyncpg.Pool,
) -> None:
    service = AuthService(
        UserRepository(clean_db),
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
    )

    first, second = await asyncio.gather(
        service.get_or_create_oauth_account(
            provider="google",
            provider_user_id="google-sub-case",
            email="  Alice@Example.com  ",
            name="Alice",
            email_verified=True,
        ),
        service.get_or_create_oauth_account(
            provider="github",
            provider_user_id="github-sub-case",
            email="alice@example.com",
            name="Alice",
            email_verified=True,
        ),
    )

    assert first.user_id == second.user_id, (
        "equivalent emails must use the same canonical identity for locking, lookup, "
        "and storage so casing or surrounding whitespace cannot create duplicate users"
    )

    rows = await clean_db.fetch(
        'SELECT id, email FROM "user" WHERE LOWER(email)=$1',
        "alice@example.com",
    )
    assert len(rows) == 1
    assert rows[0]["email"] == "alice@example.com"

    linked_accounts = await clean_db.fetchval(
        "SELECT COUNT(*) FROM oauth_accounts WHERE user_id=$1",
        first.user_id,
    )
    assert linked_accounts == 2
