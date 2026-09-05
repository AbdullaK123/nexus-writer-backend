from httpx import AsyncClient

from main import api
from src.app.dependencies import get_auth_service
from src.data.schemas.auth import UserResponse
from src.service.exceptions import AuthError
from tests.app.mocks import StubAuthService


VALID_PASSWORD = "Strong1!Password"


async def test_forgot_password_rejects_malformed_email_before_service(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/tokens/forgot-password",
        json={"email": "not-an-email"},
    )

    assert response.status_code == 422
    assert service.forgot_password_calls == []


async def test_reset_rejects_oversized_bearer_token_before_service(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/tokens/reset-password",
        json={"token": "x" * 257, "new_password": VALID_PASSWORD},
    )

    assert response.status_code == 422
    assert service.reset_password_calls == []


async def test_reset_rejects_nul_in_bearer_token_before_service(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/tokens/reset-password",
        json={"token": "abc\u0000def", "new_password": VALID_PASSWORD},
    )

    assert response.status_code == 422
    assert service.reset_password_calls == []


async def test_reset_rejects_weak_password_before_service(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/tokens/reset-password",
        json={"token": "valid-token", "new_password": "password"},
    )

    assert response.status_code == 422
    assert service.reset_password_calls == []


async def test_valid_reset_preserves_exact_opaque_token(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context
    token = "  bearer-token-with-spaces  "

    response = await client.post(
        "/api/auth/tokens/reset-password",
        json={"token": token, "new_password": VALID_PASSWORD},
    )

    assert response.status_code == 200
    assert service.reset_password_calls == [(token, VALID_PASSWORD)]


async def test_verify_requires_token_query_parameter(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.get("/api/auth/tokens/verify")

    assert response.status_code == 422
    assert service.verify_email_calls == []


async def test_verify_rejects_oversized_query_token_before_service(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.get(
        "/api/auth/tokens/verify",
        params={"token": "x" * 257},
    )

    assert response.status_code == 422
    assert service.verify_email_calls == []


async def test_valid_verification_redirects_to_success_page(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.get(
        "/api/auth/tokens/verify",
        params={"token": "valid-verification-token"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 307)
    assert response.headers["location"].endswith("/email-verified")
    assert service.verify_email_calls == ["valid-verification-token"]


async def test_invalid_verification_token_redirects_to_invalid_page(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context
    service.verify_error = AuthError("invalid token")

    response = await client.get(
        "/api/auth/tokens/verify",
        params={"token": "invalid-verification-token"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 307)
    assert response.headers["location"].endswith("/email-verified?error=invalid")


async def test_internal_verification_failure_is_not_disguised_as_invalid_token(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context
    service.verify_error = RuntimeError("database unavailable")

    response = await client.get(
        "/api/auth/tokens/verify",
        params={"token": "otherwise-valid-token"},
        follow_redirects=False,
    )

    assert response.status_code == 500, (
        "server failure must remain a server failure; redirecting to 'invalid token' "
        "would destroy observability and lie to the user about what happened"
    )
    assert "location" not in response.headers


async def test_verification_resend_requires_authentication(
    unauthenticated_client: AsyncClient,
    app_user_response: UserResponse,
) -> None:
    service = StubAuthService(app_user_response)

    async def auth_service_override() -> StubAuthService:
        return service

    api.dependency_overrides[get_auth_service] = auth_service_override

    response = await unauthenticated_client.post("/api/auth/tokens/verify-email")

    assert response.status_code == 401
    assert service.verification_email_calls == []


async def test_wrong_method_is_not_silently_accepted(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.get("/api/auth/tokens/forgot-password")

    assert response.status_code == 405
    assert service.forgot_password_calls == []
