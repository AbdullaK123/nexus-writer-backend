from datetime import datetime, timezone

from httpx import AsyncClient

from main import api
from src.app.dependencies import get_chat_service
from src.data.schemas.chat import ChatMessageListResponse, ThreadResponse


class ParentAwareChatStub:
    def __init__(self) -> None:
        self.message_calls: list[tuple[str, str, str]] = []
        self.rename_calls: list[tuple[str, str, str, str]] = []
        self.delete_calls: list[tuple[str, str, str]] = []

    async def get_thread_messages(
        self,
        story_id: str,
        thread_id: str,
        user_id: str,
    ) -> ChatMessageListResponse:
        self.message_calls.append((story_id, thread_id, user_id))
        return ChatMessageListResponse(
            thread_id=thread_id,
            thread_title="Thread",
            messages=[],
        )

    async def update_thread_title(
        self,
        story_id: str,
        thread_id: str,
        user_id: str,
        new_title: str,
    ) -> ThreadResponse:
        self.rename_calls.append((story_id, thread_id, user_id, new_title))
        return ThreadResponse(
            thread_id=thread_id,
            thread_title=new_title,
            updated_at=datetime.now(timezone.utc),
        )

    async def delete_thread(
        self,
        story_id: str,
        thread_id: str,
        user_id: str,
    ) -> dict:
        self.delete_calls.append((story_id, thread_id, user_id))
        return {"message": "deleted"}


async def test_nested_thread_reads_preserve_parent_story_at_service_boundary(
    authenticated_client: AsyncClient,
) -> None:
    service = ParentAwareChatStub()

    async def override() -> ParentAwareChatStub:
        return service

    api.dependency_overrides[get_chat_service] = override

    response = await authenticated_client.get(
        "/api/stories/story-A/chat/threads/thread-B/messages"
    )

    assert response.status_code == 200
    assert service.message_calls == [("story-A", "thread-B", "user-1")], (
        "a nested thread route must carry its parent story id downstream; otherwise a valid "
        "thread id from another story can be addressed through the wrong story URL"
    )


async def test_nested_thread_rename_preserves_parent_story_at_service_boundary(
    authenticated_client: AsyncClient,
) -> None:
    service = ParentAwareChatStub()

    async def override() -> ParentAwareChatStub:
        return service

    api.dependency_overrides[get_chat_service] = override

    response = await authenticated_client.patch(
        "/api/stories/story-A/chat/threads/thread-B",
        json={"title": "Renamed"},
    )

    assert response.status_code == 200
    assert service.rename_calls == [
        ("story-A", "thread-B", "user-1", "Renamed")
    ]


async def test_nested_thread_delete_preserves_parent_story_at_service_boundary(
    authenticated_client: AsyncClient,
) -> None:
    service = ParentAwareChatStub()

    async def override() -> ParentAwareChatStub:
        return service

    api.dependency_overrides[get_chat_service] = override

    response = await authenticated_client.delete(
        "/api/stories/story-A/chat/threads/thread-B"
    )

    assert response.status_code == 200
    assert service.delete_calls == [("story-A", "thread-B", "user-1")]
