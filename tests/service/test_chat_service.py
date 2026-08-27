import json

import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.chat import CreateThreadRequest, ConversationTurnRequest
from src.data.schemas.story import StoryRow
from src.service.chat.service import ChatService
from src.service.exceptions import NotFoundError, ValidationError
from tests.service.mocks import FakeAIProvider, FakeChatAgent, FakeChatRepository


class TestCreateThread:
    async def test_rejects_missing_story(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
    ) -> None:
        payload = CreateThreadRequest(
            story_id="missing-story",
            first_message="Help me with this story.",
        )

        with pytest.raises(NotFoundError, match="Story not found"):
            await chat_service.create_thread(test_user.id, payload)

    async def test_rejects_another_users_story(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        test_story: StoryRow,
    ) -> None:
        payload = CreateThreadRequest(
            story_id=test_story.id,
            first_message="Help me with this story.",
        )

        with pytest.raises(NotFoundError, match="Story not found"):
            await chat_service.create_thread("another-user", payload)

    async def test_persists_generated_title(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        test_story: StoryRow,
        fake_provider: FakeAIProvider,
        fake_chat_repo: FakeChatRepository,
    ) -> None:
        fake_provider.generate_response = "The Council Mystery"
        payload = CreateThreadRequest(
            story_id=test_story.id,
            first_message="Why did the council meet?",
        )

        result = await chat_service.create_thread(test_user.id, payload)
        stored = await fake_chat_repo.get_thread(result.thread_id, test_user.id)

        assert result.thread_title == "The Council Mystery"
        assert stored is not None
        assert stored.title == "The Council Mystery"

    async def test_title_failure_uses_fallback_and_still_creates_thread(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        test_story: StoryRow,
        fake_provider: FakeAIProvider,
        fake_chat_repo: FakeChatRepository,
    ) -> None:
        fake_provider.error = RuntimeError("title model unavailable")
        first_message = "Explain what happened at the eastern gate."
        payload = CreateThreadRequest(
            story_id=test_story.id,
            first_message=first_message,
        )

        result = await chat_service.create_thread(test_user.id, payload)
        stored = await fake_chat_repo.get_thread(result.thread_id, test_user.id)

        assert result.thread_title == first_message[:20] + "..."
        assert stored is not None
        assert stored.title == first_message[:20] + "..."


class TestThreadOwnership:
    async def test_cannot_rename_another_users_thread(
        self,
        chat_service: ChatService,
        chat_thread,
    ) -> None:
        with pytest.raises(NotFoundError, match="Thread not found"):
            await chat_service.update_thread_title(
                chat_thread.id,
                "another-user",
                "Stolen title",
            )

    async def test_cannot_delete_another_users_thread(
        self,
        chat_service: ChatService,
        chat_thread,
    ) -> None:
        with pytest.raises(NotFoundError, match="Thread not found"):
            await chat_service.delete_thread(chat_thread.id, "another-user")

    async def test_cannot_read_another_users_messages(
        self,
        chat_service: ChatService,
        chat_thread,
    ) -> None:
        with pytest.raises(NotFoundError, match="Thread not found"):
            await chat_service.get_thread_messages(chat_thread.id, "another-user")

    async def test_cannot_list_threads_for_another_users_story(
        self,
        chat_service: ChatService,
        test_story: StoryRow,
    ) -> None:
        with pytest.raises(NotFoundError, match="Story not found"):
            await chat_service.get_threads(test_story.id, "another-user")


class TestRunTurn:
    async def test_rejects_missing_story(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
    ) -> None:
        payload = conversation_turn.model_copy(update={"story_id": "missing-story"})

        with pytest.raises(NotFoundError, match="Story not found"):
            _ = [delta async for delta in chat_service.run_turn(test_user.id, payload)]

    async def test_rejects_missing_thread(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
    ) -> None:
        payload = conversation_turn.model_copy(update={"thread_id": "missing-thread"})

        with pytest.raises(NotFoundError, match="Thread not found"):
            _ = [delta async for delta in chat_service.run_turn(test_user.id, payload)]

    async def test_rejects_story_thread_mismatch(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        other_story: StoryRow,
        conversation_turn: ConversationTurnRequest,
    ) -> None:
        payload = conversation_turn.model_copy(update={"story_id": other_story.id})

        with pytest.raises(ValidationError) as exc_info:
            _ = [delta async for delta in chat_service.run_turn(test_user.id, payload)]

        assert exc_info.value.fields == {"story_id": ["does not match thread"]}

    async def test_streams_in_order_passes_history_and_persists_new_messages(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
        seeded_chat_history,
        chat_new_messages,
        fake_chat_agent: FakeChatAgent,
        fake_chat_repo: FakeChatRepository,
    ) -> None:
        fake_chat_agent.deltas = ["The ", "council ", "meets."]
        fake_chat_agent.messages = chat_new_messages

        deltas = [
            delta
            async for delta in chat_service.run_turn(test_user.id, conversation_turn)
        ]

        assert deltas == ["The ", "council ", "meets."]
        assert fake_chat_agent.run_count == 1
        assert fake_chat_agent.user_prompt == conversation_turn.user_message
        assert fake_chat_agent.message_history == seeded_chat_history
        assert fake_chat_agent.deps.user_id == test_user.id
        assert fake_chat_agent.deps.story_id == conversation_turn.story_id

        stored = await fake_chat_repo.list_messages(
            conversation_turn.thread_id,
            test_user.id,
        )
        assert [row.sequence for row in stored] == list(range(4))
        assert [row.kind for row in stored[-2:]] == [message.kind for message in chat_new_messages]
        assert fake_chat_repo.touched_threads == [conversation_turn.thread_id]
        assert fake_chat_repo.last_append_executor is not None
        assert fake_chat_repo.last_append_executor is fake_chat_repo.last_touch_executor

    async def test_persistence_failure_rolls_back_new_messages_and_touch(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
        chat_new_messages,
        fake_chat_agent: FakeChatAgent,
        fake_chat_repo: FakeChatRepository,
    ) -> None:
        fake_chat_agent.deltas = ["complete"]
        fake_chat_agent.messages = chat_new_messages
        fake_chat_repo.append_error_after = 1

        with pytest.raises(RuntimeError, match="append failed"):
            _ = [
                delta
                async for delta in chat_service.run_turn(test_user.id, conversation_turn)
            ]

        stored = await fake_chat_repo.list_messages(
            conversation_turn.thread_id,
            test_user.id,
        )
        assert stored == []
        assert fake_chat_repo.touched_threads == []


class TestSSE:
    async def test_success_emits_tokens_then_exactly_one_done(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
        fake_chat_agent: FakeChatAgent,
    ) -> None:
        fake_chat_agent.deltas = ["one", "two"]
        fake_chat_agent.messages = []

        frames = [
            frame
            async for frame in chat_service.stream_turn_sse(
                test_user.id,
                conversation_turn,
            )
        ]

        assert frames[:-1] == [
            chat_service._sse_frame("token", {"delta": "one"}),
            chat_service._sse_frame("token", {"delta": "two"}),
        ]
        assert frames[-1] == chat_service._sse_frame("done", {})
        assert sum(frame.startswith("event: done") for frame in frames) == 1

    async def test_service_error_emits_error_without_done(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
    ) -> None:
        payload = conversation_turn.model_copy(update={"story_id": "missing-story"})

        frames = [
            frame
            async for frame in chat_service.stream_turn_sse(test_user.id, payload)
        ]

        assert len(frames) == 1
        assert frames[0].startswith("event: error\n")
        data = json.loads(frames[0].split("data: ", 1)[1])
        assert data == {"code": "NOT_FOUND", "message": "Story not found"}
        assert not any(frame.startswith("event: done") for frame in frames)

    async def test_validation_error_includes_fields(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        other_story: StoryRow,
        conversation_turn: ConversationTurnRequest,
    ) -> None:
        payload = conversation_turn.model_copy(update={"story_id": other_story.id})

        frames = [
            frame
            async for frame in chat_service.stream_turn_sse(test_user.id, payload)
        ]

        data = json.loads(frames[0].split("data: ", 1)[1])
        assert data["code"] == "VALIDATION_ERROR"
        assert data["fields"] == {"story_id": ["does not match thread"]}
        assert not any(frame.startswith("event: done") for frame in frames)

    async def test_unexpected_agent_error_is_generic_and_does_not_leak_details(
        self,
        chat_service: ChatService,
        test_user: UserResponse,
        conversation_turn: ConversationTurnRequest,
        fake_chat_agent: FakeChatAgent,
    ) -> None:
        fake_chat_agent.error = RuntimeError("secret provider internals")

        frames = [
            frame
            async for frame in chat_service.stream_turn_sse(
                test_user.id,
                conversation_turn,
            )
        ]

        assert len(frames) == 1
        assert frames[0].startswith("event: error\n")
        data = json.loads(frames[0].split("data: ", 1)[1])
        assert data == {"code": "INTERNAL", "message": "Internal server error"}
        assert "secret provider internals" not in frames[0]
        assert not any(frame.startswith("event: done") for frame in frames)
