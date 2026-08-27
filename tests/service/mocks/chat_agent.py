from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai.messages import ModelMessage


class FakeChatAgentStream:
    def __init__(
        self,
        deltas: list[str],
        messages: list[ModelMessage],
        *,
        stream_error: Exception | None = None,
    ) -> None:
        self._deltas = deltas
        self._messages = messages
        self._stream_error = stream_error

    async def __aenter__(self) -> "FakeChatAgentStream":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def stream_text(self, *, delta: bool) -> AsyncIterator[str]:
        if self._stream_error:
            raise self._stream_error
        for chunk in self._deltas:
            yield chunk

    def new_messages(self) -> list[ModelMessage]:
        return list(self._messages)


class FakeChatAgent:
    def __init__(self) -> None:
        self.deltas: list[str] = []
        self.messages: list[ModelMessage] = []
        self.error: Exception | None = None
        self.stream_error: Exception | None = None
        self.user_prompt: str | None = None
        self.deps: Any = None
        self.message_history: list[ModelMessage] | None = None
        self.run_count = 0

    def run_stream(
        self,
        *,
        user_prompt: str,
        deps: Any,
        message_history: list[ModelMessage],
    ) -> FakeChatAgentStream:
        self.run_count += 1
        self.user_prompt = user_prompt
        self.deps = deps
        self.message_history = list(message_history)
        if self.error:
            raise self.error
        return FakeChatAgentStream(
            self.deltas,
            self.messages,
            stream_error=self.stream_error,
        )
