from typing import Any


class FakeRedis:
    def __init__(self):
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
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

    async def keys(self, pattern: str = "*") -> list[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]

    def poison(self, key: str, value: Any):
        self._store[key] = value


class FakePubSub:
    def __init__(self):
        self.published: list[tuple[str, object]] = []
        self.error: Exception | None = None

    async def publish(self, channel: str, payload: object) -> None:
        if self.error:
            raise self.error
        self.published.append((channel, payload))
