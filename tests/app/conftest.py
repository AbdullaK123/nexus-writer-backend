from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from main import api
from src.app.dependencies import get_auth_service, get_chat_service, get_current_user, get_story_service
from src.app.dependencies.redis import get_redis
from src.data.schemas.auth import UserResponse
from src.service.exceptions import AuthError
from tests.app.mocks import StubAuthService, StubChatService, StubStoryService


@pytest_asyncio.fixture
async def app_client(redis_client: Redis) -> AsyncIterator[AsyncClient]:
    api.dependency_overrides.clear()

    async def redis_override() -> Redis:
        return redis_client

    api.dependency_overrides[get_redis] = redis_override

    transport = ASGITransport(app=api, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    api.dependency_overrides.clear()


@pytest.fixture
def app_user() -> UserResponse:
    return UserResponse(
        id="user-1",
        username="controller-user",
        email="controller@example.com",
        settings={},
        profile_img=None,
        email_verified=True,
    )


@pytest.fixture
def app_user_response(app_user: UserResponse) -> UserResponse:
    return app_user.model_copy()


@pytest.fixture
def authenticated_client(
    app_client: AsyncClient,
    app_user: UserResponse,
) -> AsyncClient:
    # Chat scenarios use a subscribed account; denial cases set their own status.
    async def current_user_override() -> UserResponse:
        return app_user.model_copy(update={"subscription_status": "active"})

    api.dependency_overrides[get_current_user] = current_user_override
    return app_client


@pytest.fixture
def unauthenticated_client(app_client: AsyncClient) -> AsyncClient:
    async def current_user_override() -> UserResponse:
        raise AuthError()

    api.dependency_overrides[get_current_user] = current_user_override
    return app_client


@pytest.fixture
def auth_http_context(
    app_client: AsyncClient,
    app_user_response: UserResponse,
) -> tuple[AsyncClient, StubAuthService]:
    service = StubAuthService(app_user_response)

    async def auth_service_override() -> StubAuthService:
        return service

    api.dependency_overrides[get_auth_service] = auth_service_override
    return app_client, service


@pytest.fixture
def story_http_context(
    authenticated_client: AsyncClient,
) -> tuple[AsyncClient, StubStoryService]:
    service = StubStoryService()

    async def story_service_override() -> StubStoryService:
        return service

    api.dependency_overrides[get_story_service] = story_service_override
    return authenticated_client, service


@pytest.fixture
def chat_http_context(
    authenticated_client: AsyncClient,
) -> tuple[AsyncClient, StubChatService]:
    service = StubChatService()

    async def chat_service_override() -> StubChatService:
        return service

    api.dependency_overrides[get_chat_service] = chat_service_override
    return authenticated_client, service
