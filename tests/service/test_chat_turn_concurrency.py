from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
from uuid_extensions import uuid7str

from src.data.schemas.auth import UserResponse
from src.data.schemas.chat import ConversationTurnRequest
from src.service.chat.service import ChatService
from src.service.exceptions import ConflictError
from tests.service.mocks import FakeChatRepository


class BlockingStream:
    def __init__(self, agent: "BlockingAgent", prompt: str) -> None:
        self._agent = agent
        self._prompt = prompt

    async def __aenter__(self) -> "BlockingStream":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def stream_text(self, *, delta: bool) -> AsyncIterator[str]:
        self._agent.entered_event(self._prompt).set()
        await self._agent.release_event(self._prompt).wait()
        yield self._prompt

    def new_messages(self) -> list[Any]:
        return []


class BlockingAgent:
    def __init__(self) -> None:
        self.run_count = 0
        self._entered: dict[str, asyncio.Event] = {}
        self._release: dict[str, asyncio.Event] = {}

    def entered_event(self, prompt: str) -> asyncio.Event:
        return self._entered.setdefault(prompt, asyncio.Event())

    def release_event(self, prompt: str) -> asyncio.Event:
        return self._release.setdefault(prompt, asyncio.Event())

    def run_stream(
        self,
        *,
        user_prompt: str,
        deps: Any,
        message_history: list[Any],
    ) -> BlockingStream:
        self.run_count += 1
        return BlockingStream(self, user_prompt)


async def collect(service: ChatService, user_id: str, payload: ConversationTurnRequest) -> list[str]:
    return [delta async for delta in service.run_turn(user_id, payload)]


@pytest.mark.asyncio
async def test_same_thread_rejects_second_turn_before_it_can_generate(
    chat_service: ChatService,
    test_user: UserResponse,
    conversation_turn: ConversationTurnRequest,
) -> None:
    agent = BlockingAgent()
    chat_service._agent = agent

    first = conversation_turn.model_copy(update={"user_message": "first-turn"})
    competing = conversation_turn.model_copy(update={"user_message": "competing-turn"})

    first_task = asyncio.create_task(collect(chat_service, test_user.id, first))
    await asyncio.wait_for(agent.entered_event("first-turn").wait(), timeout=1)

    with pytest.raises(ConflictError, match="already running"):
        await collect(chat_service, test_user.id, competing)

    assert agent.run_count == 1, (
        "a competing request for the same thread must be rejected before model execution; two models generating from the same history snapshot corrupt conversational causality"
    )

    agent.release_event("first-turn").set()
    assert await first_task == ["first-turn"]


@pytest.mark.asyncio
async def test_different_threads_can_generate_concurrently(
    chat_service: ChatService,
    test_user: UserResponse,
    conversation_turn: ConversationTurnRequest,
    chat_thread,
    fake_chat_repo: FakeChatRepository,
) -> None:
    agent = BlockingAgent()
    chat_service._agent = agent

    other_thread = chat_thread.model_copy(update={"id": uuid7str()})
    fake_chat_repo.seed_thread(other_thread)

    first = conversation_turn.model_copy(update={"user_message": "thread-one"})
    second = conversation_turn.model_copy(
        update={
            "thread_id": other_thread.id,
            "user_message": "thread-two",
        }
    )

    first_task = asyncio.create_task(collect(chat_service, test_user.id, first))
    second_task = asyncio.create_task(collect(chat_service, test_user.id, second))

    await asyncio.wait_for(
        asyncio.gather(
            agent.entered_event("thread-one").wait(),
            agent.entered_event("thread-two").wait(),
        ),
        timeout=1,
    )

    assert agent.run_count == 2, (
        "chat serialization must be scoped to one thread; a global lock would unnecessarily serialize unrelated conversations"
    )

    agent.release_event("thread-one").set()
    agent.release_event("thread-two").set()
    assert await first_task == ["thread-one"]
    assert await second_task == ["thread-two"]
