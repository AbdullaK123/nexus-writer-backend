from httpx import AsyncClient

from tests.app.mocks import StubChatService


async def test_successful_turn_streams_sse_and_ends_with_done(
    chat_http_context: tuple[AsyncClient, StubChatService],
) -> None:
    client, service = chat_http_context
    service.frames = [
        'event: token\ndata: {"delta":"Hello"}\n\n',
        'event: done\ndata: {}\n\n',
    ]

    response = await client.post(
        "/api/stories/story-1/chat/threads/thread-1/turn",
        json={"firstMessage": "Continue the story"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert response.text == "".join(service.frames)
    assert response.text.count("event: done") == 1
    assert len(service.turn_calls) == 1
    user_id, payload = service.turn_calls[0]
    assert user_id == "user-1"
    assert payload.story_id == "story-1"
    assert payload.thread_id == "thread-1"
    assert payload.user_message == "Continue the story"


async def test_failed_turn_streams_error_without_false_done(
    chat_http_context: tuple[AsyncClient, StubChatService],
) -> None:
    client, service = chat_http_context
    service.frames = [
        'event: error\ndata: {"code":"NOT_FOUND","message":"Thread not found"}\n\n'
    ]

    response = await client.post(
        "/api/stories/story-1/chat/threads/thread-1/turn",
        json={"firstMessage": "Continue the story"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.startswith("event: error\n")
    assert "event: done" not in response.text
