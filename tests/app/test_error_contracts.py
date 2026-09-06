import pytest
from httpx import AsyncClient

import main
from src.service.exceptions import (
    InternalError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
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


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (NotFoundError("Story not found"), 404),
        (ValidationError({"title": ["is invalid"]}), 422),
        (RateLimitError(), 429),
    ],
)
async def test_expected_service_errors_are_not_reported_to_sentry(
    story_http_context: tuple[AsyncClient, StubStoryService],
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
) -> None:
    client, service = story_http_context
    captured: list[BaseException] = []
    monkeypatch.setattr(main.sentry_sdk, "capture_exception", captured.append)
    service.error = error

    response = await client.get("/api/stories/story-1")

    assert response.status_code == expected_status
    assert captured == []


async def test_internal_service_error_is_reported_to_sentry(
    story_http_context: tuple[AsyncClient, StubStoryService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, service = story_http_context
    captured: list[BaseException] = []
    monkeypatch.setattr(main.sentry_sdk, "capture_exception", captured.append)
    error = InternalError("server failed")
    service.error = error

    response = await client.get("/api/stories/story-1")

    assert response.status_code == 500
    assert captured == [error]


async def test_unhandled_exception_returns_generic_500_without_leaking_details(
    story_http_context: tuple[AsyncClient, StubStoryService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, service = story_http_context
    captured: list[BaseException] = []
    monkeypatch.setattr(main.sentry_sdk, "capture_exception", captured.append)
    error = RuntimeError("secret database internals")
    service.error = error

    response = await client.get("/api/stories/story-1")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal Server Error"
    assert "correlation_id" in body
    assert "secret database internals" not in response.text
    assert captured == [error]
