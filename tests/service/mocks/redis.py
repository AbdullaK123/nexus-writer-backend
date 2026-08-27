from datetime import timedelta
from typing import Any


class FakeRedis:
    def __init__(self):
        self._store: dict[str, Any] = {}
        self.set_calls: list[tuple[str, Any, int | timedelta | None]] = []

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        *,
        ex: int | timedelta | None = None,
        nx: bool = False,
    ) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        self.set_calls.append((key, value, ex))
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                count += 1
        return count

    async def flush(self):
        self._store.clear()
        self.set_calls.clear()

    async def keys(self, pattern: str = "*") -> list[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]

    def poison(self, key: str, value: Any):
        self._store[key] = value

    def peek(self, key: str) -> Any | None:
        return self._store.get(key)


class FakePubSub:
    def __init__(self):
        self.published: list[tuple[str, object]] = []
        self.error: Exception | None = None

    async def publish(self, channel: str, payload: object) -> None:
        if self.error:
            raise self.error
        self.published.append((channel, payload))
