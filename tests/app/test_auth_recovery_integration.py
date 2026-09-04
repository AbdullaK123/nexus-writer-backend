import asyncio
import re

import asyncpg
from httpx import AsyncClient
import pytest

from main import api
from src.app.dependencies import get_auth_service
from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.user import UserRepository
from src.infrastructure.auth.password import hash_password
from src.service.auth.service import AuthService


OLD_PASSWORD = "Original1!Password"
NEW_PASSWORD = "Replacement2!Password"
RACE_PASSWORD_A = "CandidateA3!Password"
RACE_PASSWORD_B = "CandidateB4!Password"


def build_service(pool: asyncpg.Pool) -> AuthService:
    return AuthService(
        UserRepository(pool),
        SessionRepository(pool),
        AuthTokenRepository(pool),
        None,  # type: ignore[arg-type]
    )


def extract_token(html: str, marker: str) -> str:
    match = re.search(rf"{re.escape(marker)}([^&\"<]+)", html)
    assert match is not None, f"expected email HTML to contain token marker {marker!r}"
    return match.group(1)


async def install_real_auth_service(pool: asyncpg.Pool) -> AuthService:
    service = build_service(pool)

    async def auth_service_override() -> AuthService:
        return service

    api.dependency_overrides[get_auth_service] = auth_service_override
    return service


async def test_complete_registration_verification_and_password_recovery_flow(
    app_client: AsyncClient,
    clean_db: asyncpg.Pool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await install_real_auth_service(clean_db)
    sent_emails: list[dict] = []

    async def capture_email(payload: dict) -> dict:
        sent_emails.append(payload)
        return {"id": f"email-{len(sent_emails)}"}

    monkeypatch.setattr("src.service.auth.service.resend.Emails.send_async", capture_email)

    register = await app_client.post(
        "/api/auth/register",
        json={
            "username": "recovery-user",
            "email": "recovery@example.com",
            "password": OLD_PASSWORD,
        },
    )
    assert register.status_code == 200
    user_id = register.json()["id"]
    assert await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user_id
    ) is False
    assert len(sent_emails) == 1

    verification_token = extract_token(
        sent_emails[-1]["html"],
        "/api/auth/tokens/verify?token=",
    )
    verify = await app_client.get(
        "/api/auth/tokens/verify",
        params={"token": verification_token},
        follow_redirects=False,
    )
    assert verify.status_code in (302, 307)
    assert verify.headers["location"].endswith("/email-verified")
    assert await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user_id
    ) is True

    first_login = await app_client.post(
        "/api/auth/login",
        json={"email": "recovery@example.com", "password": OLD_PASSWORD},
    )
    second_login = await app_client.post(
        "/api/auth/login",
        json={"email": "recovery@example.com", "password": OLD_PASSWORD},
    )
    assert first_login.status_code == 200
    assert second_login.status_code == 200
    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM "session" WHERE user_id=$1', user_id
    ) == 2

    forgot = await app_client.post(
        "/api/auth/tokens/forgot-password",
        json={"email": "recovery@example.com"},
    )
    assert forgot.status_code == 200
    assert len(sent_emails) == 2
    reset_token = extract_token(
        sent_emails[-1]["html"],
        "/reset-password?token=",
    )

    reset = await app_client.post(
        "/api/auth/tokens/reset-password",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )
    assert reset.status_code == 200
    assert await clean_db.fetchval(
        'SELECT COUNT(*) FROM "session" WHERE user_id=$1', user_id
    ) == 0, "successful password recovery must revoke every pre-reset session"

    old_login = await app_client.post(
        "/api/auth/login",
        json={"email": "recovery@example.com", "password": OLD_PASSWORD},
    )
    new_login = await app_client.post(
        "/api/auth/login",
        json={"email": "recovery@example.com", "password": NEW_PASSWORD},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200

    replay = await app_client.post(
        "/api/auth/tokens/reset-password",
        json={"token": reset_token, "new_password": "Replay5!Password"},
    )
    assert replay.status_code == 401


async def test_http_concurrent_password_reset_has_exactly_one_credential_winner(
    app_client: AsyncClient,
    clean_db: asyncpg.Pool,
) -> None:
    await install_real_auth_service(clean_db)
    user = await UserRepository(clean_db).create(
        username="http-reset-race",
        email="http-reset-race@example.com",
        password_hash=hash_password(OLD_PASSWORD),
        profile_img=None,
        verified=True,
    )
    token = await AuthTokenRepository(clean_db).create(
        user_id=user.id,
        purpose="password_reset",
    )

    async def reset(password: str):
        return await app_client.post(
            "/api/auth/tokens/reset-password",
            json={"token": token, "new_password": password},
        )

    response_a, response_b = await asyncio.gather(
        reset(RACE_PASSWORD_A),
        reset(RACE_PASSWORD_B),
    )

    assert sorted([response_a.status_code, response_b.status_code]) == [200, 401], (
        "the HTTP boundary must expose one successful token consumer and one replay loser"
    )

    login_a = await app_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": RACE_PASSWORD_A},
    )
    login_b = await app_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": RACE_PASSWORD_B},
    )

    assert sorted([login_a.status_code, login_b.status_code]) == [200, 401], (
        "exactly one of the concurrently proposed passwords may become the canonical credential"
    )
