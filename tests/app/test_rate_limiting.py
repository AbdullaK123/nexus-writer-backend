from httpx import AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError

from main import api
from src.app.dependencies.redis import get_redis
from tests.app.mocks import StubAuthService


REGISTRATION = {
    "username": "controller-user",
    "email": "controller@example.com",
    "password": "StrongPass123!",
}


async def test_register_returns_429_after_exact_ip_limit(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    for _ in range(5):
        response = await client.post("/api/auth/register", json=REGISTRATION)
        assert response.status_code == 200

    blocked = await client.post("/api/auth/register", json=REGISTRATION)

    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "RATE_LIMITED"
    assert len(service.registration_calls) == 5


async def test_auth_operations_do_not_share_one_bucket(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    for _ in range(5):
        response = await client.post("/api/auth/register", json=REGISTRATION)
        assert response.status_code == 200

    forgot = await client.post(
        "/api/auth/tokens/forgot-password",
        json={"email": "controller@example.com"},
    )

    assert forgot.status_code == 200
    assert service.forgot_password_calls == ["controller@example.com"]


async def test_spoofed_x_real_ip_does_not_bypass_limit(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    for index in range(5):
        response = await client.post(
            "/api/auth/register",
            json=REGISTRATION,
            headers={"X-Real-IP": f"203.0.113.{index + 1}"},
        )
        assert response.status_code == 200

    blocked = await client.post(
        "/api/auth/register",
        json=REGISTRATION,
        headers={"X-Real-IP": "198.51.100.99"},
    )

    assert blocked.status_code == 429
    assert len(service.registration_calls) == 5


async def test_rate_limiting_fails_open_when_redis_is_unavailable(
    auth_http_context: tuple[AsyncClient, StubAuthService],
) -> None:
    client, service = auth_http_context

    class BrokenRedis:
        async def eval(self, *args, **kwargs):
            raise RedisConnectionError("redis unavailable")

    async def broken_redis():
        return BrokenRedis()

    api.dependency_overrides[get_redis] = broken_redis

    response = await client.post("/api/auth/register", json=REGISTRATION)

    assert response.status_code == 200
    assert len(service.registration_calls) == 1
