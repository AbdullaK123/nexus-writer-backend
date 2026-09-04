import asyncpg
import pytest

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.user import UserRepository
from src.infrastructure.auth.password import hash_password
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError


def build_service(pool: asyncpg.Pool) -> AuthService:
    return AuthService(
        UserRepository(pool),
        SessionRepository(pool),
        AuthTokenRepository(pool),
        None,  # type: ignore[arg-type]
    )


async def test_unverified_oauth_email_assertion_cannot_create_or_link_identity(
    clean_db: asyncpg.Pool,
) -> None:
    service = build_service(clean_db)

    with pytest.raises(AuthError, match="did not verify"):
        await service.get_or_create_oauth_account(
            provider="google",
            provider_user_id="unverified-provider-sub",
            email="unverified-provider@example.com",
            name="Unverified Provider User",
            email_verified=False,
        )

    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM "user" WHERE email=$1',
        "unverified-provider@example.com",
    ) == 0
    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM oauth_accounts WHERE provider_user_id=$1',
        "unverified-provider-sub",
    ) == 0


async def test_verified_oauth_link_marks_existing_password_account_verified(
    clean_db: asyncpg.Pool,
) -> None:
    repo = UserRepository(clean_db)
    user = await repo.create(
        username="local-before-oauth",
        email="local-before-oauth@example.com",
        password_hash=hash_password("Strong1!Password"),
        profile_img=None,
        verified=False,
    )
    service = build_service(clean_db)

    account = await service.get_or_create_oauth_account(
        provider="google",
        provider_user_id="verified-link-sub",
        email="local-before-oauth@example.com",
        name="Local Before OAuth",
        email_verified=True,
    )

    assert account.user_id == user.id
    assert await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    ) is True


async def test_existing_oauth_account_reasserts_verified_email_state(
    clean_db: asyncpg.Pool,
) -> None:
    service = build_service(clean_db)
    account = await service.get_or_create_oauth_account(
        provider="google",
        provider_user_id="existing-verified-sub",
        email="existing-verified@example.com",
        name="Existing OAuth User",
        email_verified=True,
    )
    await clean_db.execute(
        'UPDATE "user" SET email_verified=FALSE WHERE id=$1',
        account.user_id,
    )

    again = await service.get_or_create_oauth_account(
        provider="google",
        provider_user_id="existing-verified-sub",
        email="existing-verified@example.com",
        name="Existing OAuth User",
        email_verified=True,
    )

    assert again.id == account.id
    assert await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', account.user_id
    ) is True
