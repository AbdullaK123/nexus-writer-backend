import asyncio

from src.data.repositories.chat import ChatRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chat import ChatThreadRow


REQUEST_A = {"kind": "request", "parts": [{"content": "A"}]}
REQUEST_B = {"kind": "request", "parts": [{"content": "B"}]}


async def test_concurrent_message_appends_preserve_unique_contiguous_sequence(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
) -> None:
    """Two independent requests must not both compute MAX(sequence) + 1 as the same value."""
    ready = asyncio.Event()
    waiting = 0
    lock = asyncio.Lock()

    async def append(message: dict):
        nonlocal waiting
        async with chat_repo.pool.acquire() as conn:
            async with conn.transaction():
                async with lock:
                    waiting += 1
                    if waiting == 2:
                        ready.set()
                await ready.wait()
                return await chat_repo.append_message(
                    repo_chat_thread.id,
                    repo_user.id,
                    "request",
                    message,
                    executor=conn,
                )

    first, second = await asyncio.gather(
        append(REQUEST_A),
        append(REQUEST_B),
    )

    rows = await chat_repo.list_messages(repo_chat_thread.id, repo_user.id)
    sequences = [row.sequence for row in rows]

    assert len(rows) == 2
    assert sequences == [0, 1], (
        "concurrent appends must serialize sequence allocation; duplicate or gapped "
        "sequence numbers corrupt canonical conversation history"
    )
    assert {first.sequence, second.sequence} == {0, 1}
