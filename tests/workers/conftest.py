from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import cron_worker
import saq_worker
from tests.workers.mocks import (
    FakeAnalyticsService,
    FakeChapterRepository,
    FakeChapterService,
    FakeCronEmbeddingService,
    FakeEmbeddingService,
    FakeExtractionService,
    FakeHeartbeatPath,
    FakePubSub,
    FakeRedisClient,
    FakeReextractionService,
    FakeSessionCleanupService,
    FakeStoryService,
    FakeWorker,
)


@pytest.fixture
def job_ids() -> dict[str, str]:
    return {
        "chapter_id": "11111111-1111-4111-8111-111111111111",
        "story_id": "22222222-2222-4222-8222-222222222222",
        "user_id": "33333333-3333-4333-8333-333333333333",
    }


@pytest.fixture
def fake_worker_services() -> dict[str, Any]:
    return {
        "chapter_repo": FakeChapterRepository(),
        "extraction_service": FakeExtractionService(),
        "embedding_service": FakeEmbeddingService(),
        "story_service": FakeStoryService(),
        "chapter_service": FakeChapterService(),
        "analytics_service": FakeAnalyticsService(),
        "pubsub": FakePubSub(),
    }


@pytest.fixture
def fake_redis_client() -> FakeRedisClient:
    return FakeRedisClient()


@pytest.fixture
def saq_context(
    fake_worker_services: dict[str, Any],
    fake_redis_client: FakeRedisClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    monkeypatch.setattr(saq_worker, "client", fake_redis_client)
    monkeypatch.setattr(saq_worker, "HEARTBEAT_FILE", tmp_path / "saq-heartbeat")
    return {"worker": FakeWorker(fake_worker_services)}


@pytest.fixture
def cron_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> SimpleNamespace:
    heartbeat = FakeHeartbeatPath()
    session_cleanup = FakeSessionCleanupService()
    reextraction = FakeReextractionService()
    embedding = FakeCronEmbeddingService()

    monkeypatch.setattr(cron_worker, "HEARTBEAT_FILE", heartbeat)
    monkeypatch.setattr(cron_worker, "get_pool", lambda: object())
    monkeypatch.setattr(cron_worker, "build_ai_provider", lambda: object())
    monkeypatch.setattr(cron_worker, "UserRepository", lambda pool: object())
    monkeypatch.setattr(cron_worker, "SessionRepository", lambda pool: object())
    monkeypatch.setattr(cron_worker, "ChapterRepository", lambda pool: object())
    monkeypatch.setattr(cron_worker, "SceneRepository", lambda pool: object())
    monkeypatch.setattr(cron_worker, "AuthService", lambda *args: session_cleanup)
    monkeypatch.setattr(cron_worker, "ExtractionService", lambda *args, **kwargs: reextraction)
    monkeypatch.setattr(cron_worker, "EmbeddingService", lambda *args, **kwargs: embedding)

    return SimpleNamespace(
        heartbeat=heartbeat,
        session_cleanup=session_cleanup,
        reextraction=reextraction,
        embedding=embedding,
    )
