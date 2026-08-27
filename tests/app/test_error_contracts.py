from httpx import AsyncClient

from src.service.exceptions import NotFoundError, ValidationError
from tests.app.mocks import StubStoryService


async def test_service_not_found_maps_to_404(
    story_http_context: tuple[AsyncClient, StubStoryService],
) -> None:
    client, service = story_http_context
    service.error = NotFoundError("Story not found")

    response = await client.get("/api/stories/missing-story")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "NOT_FOUND"
    assert detail["message"] == "Story not found"
    assert "correlation_id" in detail


async def test_service_validation_error_maps_fields_to_422(
    story_http_context: tuple[AsyncClient, StubStoryService],
) -> None:
    client, service = story_http_context
    service.error = ValidationError({"title": ["is invalid"]})

    response = await client.get("/api/stories/story-1")

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "VALIDATION_ERROR"
    assert detail["fields"] == {"title": ["is invalid"]}


async def test_unhandled_exception_returns_generic_500_without_leaking_details(
    story_http_context: tuple[AsyncClient, StubStoryService],
) -> None:
    client, service = story_http_context
    service.error = RuntimeError("secret database internals")

    response = await client.get("/api/stories/story-1")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal Server Error"
    assert "correlation_id" in body
    assert "secret database internals" not in response.text
