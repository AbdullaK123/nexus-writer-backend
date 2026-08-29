from httpx import AsyncClient

from src.shared.text_types import CHAT_MESSAGE_MAX
from tests.app.mocks import StubChatService


async def test_chat_turn_rejects_nul_as_request_validation_error_before_service(
    chat_http_context: tuple[AsyncClient, StubChatService],
) -> None:
    client, service = chat_http_context

    response = await client.post(
        "/api/stories/story-1/chat/threads/thread-1/turn",
        json={"userMessage": "safe\u0000poison"},
    )

    assert response.status_code == 422, (
        "hostile text must fail at the HTTP schema boundary; a Pydantic validation "
        "error raised manually inside the route must not escape as a 500"
    )
    assert service.turn_calls == []


async def test_chat_turn_rejects_oversized_prompt_before_service(
    chat_http_context: tuple[AsyncClient, StubChatService],
) -> None:
    client, service = chat_http_context

    response = await client.post(
        "/api/stories/story-1/chat/threads/thread-1/turn",
        json={"userMessage": "x" * (CHAT_MESSAGE_MAX + 1)},
    )

    assert response.status_code == 422
    assert service.turn_calls == []


async def test_chat_turn_rejects_whitespace_only_prompt_before_service(
    chat_http_context: tuple[AsyncClient, StubChatService],
) -> None:
    client, service = chat_http_context

    response = await client.post(
        "/api/stories/story-1/chat/threads/thread-1/turn",
        json={"userMessage": " \t\r\n "},
    )

    assert response.status_code == 422
    assert service.turn_calls == []
