from types import SimpleNamespace
from typing import Any


class FakeRedisClient:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.set_calls: list[tuple[str, Any]] = []

    async def delete(self, key: str) -> None:
        self.deleted.append(key)

    async def set(self, key: str, value: Any) -> None:
        self.set_calls.append((key, value))


class FakePubSub:
    def __init__(self) -> None:
        self.published: list[tuple[str, Any]] = []

    async def publish(self, channel: str, message: Any) -> None:
        self.published.append((channel, message))


class FakeChapterRepository:
    def __init__(self) -> None:
        self.rows: list[Any] = []
        self.calls: list[tuple[str, str]] = []

    async def get(self, chapter_id: str, user_id: str) -> Any:
        self.calls.append((chapter_id, user_id))
        if self.rows:
            return self.rows.pop(0)
        return None


class FakeExtractionService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.result: Any = SimpleNamespace(
            scenes_extracted=2,
            chapter_number=3,
            story_title="Test Story",
        )
        self.error: Exception | None = None

    async def extract_scenes(
        self,
        chapter_id: str,
        user_id: str,
        content: str | None,
    ) -> Any:
        self.calls.append((chapter_id, user_id, content))
        if self.error:
            raise self.error
        return self.result


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.error: Exception | None = None

    async def embed_scenes(self, chapter_id: str) -> None:
        self.calls.append(chapter_id)
        if self.error:
            raise self.error


class FakeStoryService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.error: Exception | None = None

    async def get_pulse(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self.error:
            raise self.error


class FakeAnalyticsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.error: Exception | None = None

    async def _record(self, name: str, **kwargs: Any) -> None:
        self.calls.append((name, kwargs))
        if self.error:
            raise self.error

    async def extract_plot_threads(self, **kwargs: Any) -> None:
        await self._record("extract_plot_threads", **kwargs)

    async def extract_acts(self, **kwargs: Any) -> None:
        await self._record("extract_acts", **kwargs)

    async def extract_contradictions(self, **kwargs: Any) -> None:
        await self._record("extract_contradictions", **kwargs)

    async def extract_entities(self, **kwargs: Any) -> None:
        await self._record("extract_entities", **kwargs)


class FakeChapterService:
    def __init__(self) -> None:
        self.summary_calls: list[dict[str, Any]] = []
        self.comment_calls: list[tuple[str, str, bool]] = []
        self.summary_error: Exception | None = None
        self.comment_error: Exception | None = None
        self.comments_result: Any = SimpleNamespace(
            extraction=SimpleNamespace(comments=[1, 2]),
            chapter_number=3,
            story_title="Test Story",
        )

    async def summarize_chapter(self, **kwargs: Any) -> None:
        self.summary_calls.append(kwargs)
        if self.summary_error:
            raise self.summary_error

    async def generate_comments(
        self,
        user_id: str,
        chapter_id: str,
        ignore_cache: bool = False,
    ) -> Any:
        self.comment_calls.append((user_id, chapter_id, ignore_cache))
        if self.comment_error:
            raise self.comment_error
        return self.comments_result


class FakeWorker:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
