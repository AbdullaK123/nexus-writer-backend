from httpx import AsyncClient

from tests.app.mocks import StubAuthService


async def test_valid_registration_maps_to_success_response(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/register",
        json={
            "username": "controller-user",
            "email": "controller@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == "user-1"
    assert response.json()["username"] == "controller-user"
    assert len(service.registration_calls) == 1


async def test_invalid_registration_body_returns_422(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    response = await client.post(
        "/api/auth/register",
        json={"username": "x", "email": "not-an-email", "password": "weak"},
    )

    assert response.status_code == 422
    assert service.registration_calls == []


async def test_missing_authentication_returns_401(
    unauthenticated_client: AsyncClient,
) -> None:
    response = await unauthenticated_client.get("/api/auth/me")

    assert response.status_code == 401
    detail = response.json()["detail"]
    assert detail["code"] == "UNAUTHORIZED"
    assert detail["message"] == "Authentication required"
