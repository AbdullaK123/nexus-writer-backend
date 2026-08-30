from copy import deepcopy
from datetime import datetime, timezone
from typing import Literal

from uuid_extensions import uuid7str

from src.data.schemas.chat import ChatMessageRow, ChatThreadRow


def _now() -> datetime:
    return datetime.now(timezone.utc)


class _ChatTransaction:
    def __init__(self, repo: "FakeChatRepository") -> None:
        self._repo = repo
        self._threads: dict[str, ChatThreadRow] = {}
        self._messages: dict[str, list[ChatMessageRow]] = {}
        self._touches: list[str] = []

    async def __aenter__(self) -> "_ChatTransaction":
        self._threads = deepcopy(self._repo._threads)
        self._messages = deepcopy(self._repo._messages)
        self._touches = list(self._repo.touched_threads)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._repo._threads = self._threads
            self._repo._messages = self._messages
            self._repo.touched_threads = self._touches
        return False


class _ChatConnection:
    def __init__(self, repo: "FakeChatRepository") -> None:
        self._repo = repo

    def transaction(self) -> _ChatTransaction:
        return _ChatTransaction(self._repo)

    async def fetchval(self, sql: str, lock_key: str):
        if "pg_try_advisory_lock" not in sql:
            raise AssertionError(f"unexpected fetchval SQL: {sql}")
        if lock_key in self._repo._turn_locks:
            return False
        self._repo._turn_locks.add(lock_key)
        return True

    async def execute(self, sql: str, lock_key: str):
        if "pg_advisory_unlock" not in sql:
            raise AssertionError(f"unexpected execute SQL: {sql}")
        self._repo._turn_locks.discard(lock_key)
        return "SELECT 1"


class _ChatAcquireContext:
    def __init__(self, repo: "FakeChatRepository") -> None:
        self._connection = _ChatConnection(repo)

    async def __aenter__(self) -> _ChatConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _ChatPool:
    def __init__(self, repo: "FakeChatRepository") -> None:
        self._repo = repo

    def acquire(self) -> _ChatAcquireContext:
        return _ChatAcquireContext(self._repo)


class FakeChatRepository:
    def __init__(self) -> None:
        self._threads: dict[str, ChatThreadRow] = {}
        self._messages: dict[str, list[ChatMessageRow]] = {}
        self._turn_locks: set[str] = set()
        self.error: Exception | None = None
        self.append_error_after: int | None = None
        self.touch_error: Exception | None = None
        self.append_count = 0
        self.touched_threads: list[str] = []
        self.last_append_executor = None
        self.last_touch_executor = None
        self.pool = _ChatPool(self)

    def seed_thread(self, thread: ChatThreadRow) -> None:
        self._threads[thread.id] = thread
        self._messages.setdefault(thread.id, [])

    def seed_message(self, message: ChatMessageRow) -> None:
        self._messages.setdefault(message.thread_id, []).append(message)
        self._messages[message.thread_id].sort(key=lambda row: row.sequence)

    async def create_thread(
        self,
        user_id: str,
        story_id: str,
        title: str,
        executor=None,
    ) -> ChatThreadRow:
        if self.error:
            raise self.error
        now = _now()
        thread = ChatThreadRow(
            id=uuid7str(),
            user_id=user_id,
            story_id=story_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        self.seed_thread(thread)
        return thread

    async def get_thread(
        self,
        thread_id: str,
        user_id: str,
        executor=None,
    ) -> ChatThreadRow | None:
        if self.error:
            raise self.error
        thread = self._threads.get(thread_id)
        if thread is not None and thread.user_id == user_id:
            return thread
        return None

    async def list_threads_for_story(
        self,
        user_id: str,
        story_id: str,
        executor=None,
    ) -> list[ChatThreadRow]:
        if self.error:
            raise self.error
        rows = [
            thread
            for thread in self._threads.values()
            if thread.user_id == user_id and thread.story_id == story_id
        ]
        return sorted(rows, key=lambda row: row.updated_at, reverse=True)

    async def update_thread_title(
        self,
        thread_id: str,
        user_id: str,
        title: str,
        *,
        executor=None,
    ) -> ChatThreadRow | None:
        if self.error:
            raise self.error
        thread = await self.get_thread(thread_id, user_id, executor=executor)
        if thread is None:
            return None
        updated = thread.model_copy(update={"title": title, "updated_at": _now()})
        self._threads[thread_id] = updated
        return updated

    async def touch_thread(
        self,
        thread_id: str,
        user_id: str,
        *,
        executor=None,
    ) -> None:
        self.last_touch_executor = executor
        if self.touch_error:
            raise self.touch_error
        if self.error:
            raise self.error
        thread = await self.get_thread(thread_id, user_id, executor=executor)
        if thread is not None:
            self._threads[thread_id] = thread.model_copy(update={"updated_at": _now()})
            self.touched_threads.append(thread_id)

    async def delete_thread(
        self,
        thread_id: str,
        user_id: str,
        *,
        executor=None,
    ) -> None:
        if self.error:
            raise self.error
        thread = await self.get_thread(thread_id, user_id, executor=executor)
        if thread is not None:
            self._threads.pop(thread_id, None)
            self._messages.pop(thread_id, None)

    async def append_message(
        self,
        thread_id: str,
        user_id: str,
        kind: Literal["request", "response"],
        message: dict,
        *,
        executor=None,
    ) -> ChatMessageRow:
        self.last_append_executor = executor
        if self.error:
            raise self.error
        if self.append_error_after is not None and self.append_count >= self.append_error_after:
            raise RuntimeError("append failed")

        rows = self._messages.setdefault(thread_id, [])
        row = ChatMessageRow(
            id=uuid7str(),
            thread_id=thread_id,
            user_id=user_id,
            sequence=len(rows),
            kind=kind,
            message=message,
            created_at=_now(),
        )
        rows.append(row)
        self.append_count += 1
        return row

    async def list_messages(
        self,
        thread_id: str,
        user_id: str,
        *,
        executor=None,
    ) -> list[ChatMessageRow]:
        if self.error:
            raise self.error
        thread = await self.get_thread(thread_id, user_id, executor=executor)
        if thread is None:
            return []
        return sorted(self._messages.get(thread_id, []), key=lambda row: row.sequence)
