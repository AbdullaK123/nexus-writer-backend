from collections.abc import AsyncIterator

from src.data.schemas.chat import ConversationTurnRequest


class StubChatService:
    def __init__(self) -> None:
        self.frames: list[str] = []
        self.turn_calls: list[tuple[str, ConversationTurnRequest]] = []

    async def stream_turn_sse(
        self,
        user_id: str,
        payload: ConversationTurnRequest,
    ) -> AsyncIterator[str]:
        self.turn_calls.append((user_id, payload))
        for frame in self.frames:
            yield frame
