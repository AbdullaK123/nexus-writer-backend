from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from src.data.schemas.auth import Notification
from src.data.schemas.extraction import SceneExtractionResult


@dataclass
class PublishedChapter:
    id: str
    story_id: str
    content: str = "chapter text"
    published: bool = True


class FakeRedisClient:
    def __init__(self) -> None:
        self.set_calls: list[tuple[str, str]] = []
        self.delete_calls: list[str] = []

    async def set(self, key: str, value: str) -> None:
        self.set_calls.append((key, value))

    async def delete(self, key: str) -> None:
        self.delete_calls.append(key)


class FakePubSub:
    def __init__(self) -> None:
        self.published: list[tuple[str, Notification]] = []

    async def publish(self, channel: str, notification: Notification) -> None:
        self.published.append((channel, notification))


class FakeChapterRepository:
    def __init__(self) -> None:
        self.rows: list[PublishedChapter | None] = []
        self.get_calls: list[tuple[str, str]] = []

    async def get(self, chapter_id: str, user_id: str) -> PublishedChapter | None:
        self.get_calls.append((chapter_id, user_id))
        if self.rows:
            return self.rows.pop(0)
        return None


class FakeExtractionService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.result: SceneExtractionResult | None = SceneExtractionResult(
            scenes_extracted=2,
            chapter_number=3,
            story_title="Test Story",
        )
        self.error: Exception | None = None

    async def extract_scenes(self, chapter_id: str, user_id: str, content: str | None = None) -> SceneExtractionResult | None:
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
        self.pulse_calls: list[dict[str, Any]] = []
        self.error: Exception | None = None

    async def get_pulse(self, **kwargs: Any) -> None:
        self.pulse_calls.append(kwargs)
        if self.error:
            raise self.error


class FakeChapterService:
    def __init__(self) -> None:
        self.summary_calls: list[dict[str, Any]] = []
        self.comment_calls: list[tuple[str, str, bool]] = []
        self.summary_error: Exception | None = None
        self.comment_error: Exception | None = None

    async def summarize_chapter(self, **kwargs: Any) -> None:
        self.summary_calls.append(kwargs)
        if self.summary_error:
            raise self.summary_error

    async def generate_comments(self, user_id: str, chapter_id: str, *, ignore_cache: bool) -> Any:
        self.comment_calls.append((user_id, chapter_id, ignore_cache))
        if self.comment_error:
            raise self.comment_error
        return SimpleNamespace(
            extraction=SimpleNamespace(comments=[object(), object()]),
            chapter_number=3,
            story_title="Test Story",
        )


class FakeAnalyticsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.error: Exception | None = None

    async def _record(self, name: str, **kwargs: Any) -> None:
        self.calls.append((name, kwargs))
        if self.error:
            raise self.error

    async def extract_plot_threads(self, **kwargs: Any) -> None:
        await self._record("plot", **kwargs)

    async def extract_acts(self, **kwargs: Any) -> None:
        await self._record("acts", **kwargs)

    async def extract_contradictions(self, **kwargs: Any) -> None:
        await self._record("contradictions", **kwargs)

    async def extract_entities(self, **kwargs: Any) -> None:
        await self._record("entities", **kwargs)


class FakeWorker:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
