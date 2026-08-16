# tests/service/conftest.py

import pytest
from src.infrastructure.config.settings import SearchConfig
from src.service.story.service import StoryService
from src.service.chapter.service import ChapterService
from src.service.auth.service import AuthService
from src.service.extraction.service import ExtractionService
from src.service.embedding.service import EmbeddingService
from src.service.analytics.service import AnalyticsService

from tests.service.mocks import (
    FakeRedis,
    FakePubSub,
    FakeAIProvider,
    FakeUserRepository,
    FakeSessionRepository,
    FakeStoryRepository,
    FakeChapterRepository,
    FakeSceneRepository,
    FakeAnalyticsRepository,
    FakeChatRepository,
)


# ── Infrastructure fakes ─────────────────────────────

@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def fake_pubsub() -> FakePubSub:
    return FakePubSub()


@pytest.fixture
def fake_provider() -> FakeAIProvider:
    return FakeAIProvider()


@pytest.fixture
def search_config() -> SearchConfig:
    return SearchConfig()


# ── Repository fakes ─────────────────────────────────

@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_session_repo() -> FakeSessionRepository:
    return FakeSessionRepository()


@pytest.fixture
def fake_story_repo() -> FakeStoryRepository:
    return FakeStoryRepository()


@pytest.fixture
def fake_chapter_repo() -> FakeChapterRepository:
    return FakeChapterRepository()


@pytest.fixture
def fake_scene_repo() -> FakeSceneRepository:
    return FakeSceneRepository()


@pytest.fixture
def fake_analytics_repo() -> FakeAnalyticsRepository:
    return FakeAnalyticsRepository()


@pytest.fixture
def fake_chat_repo() -> FakeChatRepository:
    return FakeChatRepository()


# ── Service fixtures ─────────────────────────────────

@pytest.fixture
def story_service(
    fake_story_repo,
    fake_chapter_repo,
    fake_scene_repo,
    fake_provider,
    search_config,
    fake_redis,
) -> StoryService:
    return StoryService(
        story_repo=fake_story_repo,
        chapter_repo=fake_chapter_repo,
        scene_repo=fake_scene_repo,
        provider=fake_provider,
        search_config=search_config,
        redis=fake_redis,
    )


@pytest.fixture
def chapter_service(
    fake_story_repo,
    fake_chapter_repo,
    fake_scene_repo,
    fake_analytics_repo,
    fake_provider,
    fake_redis,
) -> ChapterService:
    return ChapterService(
        story_repo=fake_story_repo,
        chapter_repo=fake_chapter_repo,
        scene_repo=fake_scene_repo,
        analytics_repo=fake_analytics_repo,
        provider=fake_provider,
        redis=fake_redis,
    )


@pytest.fixture
def auth_service(
    fake_user_repo,
    fake_session_repo,
    fake_pubsub,
) -> AuthService:
    return AuthService(
        user_repo=fake_user_repo,
        session_repo=fake_session_repo,
        pubsub=fake_pubsub,
    )


@pytest.fixture
def extraction_service(
    fake_provider,
    fake_chapter_repo,
    fake_scene_repo,
) -> ExtractionService:
    return ExtractionService(
        provider=fake_provider,
        chapter_repo=fake_chapter_repo,
        scene_repo=fake_scene_repo,
    )


@pytest.fixture
def embedding_service(
    fake_scene_repo,
    fake_provider,
) -> EmbeddingService:
    return EmbeddingService(
        scene_repo=fake_scene_repo,
        provider=fake_provider,
    )


@pytest.fixture
def analytics_service(
    fake_analytics_repo,
    fake_story_repo,
    fake_chapter_repo,
    fake_scene_repo,
    fake_provider,
    fake_redis,
) -> AnalyticsService:
    return AnalyticsService(
        analytics_repo=fake_analytics_repo,
        story_repo=fake_story_repo,
        chapter_repo=fake_chapter_repo,
        scene_repo=fake_scene_repo,
        provider=fake_provider,
        redis=fake_redis,
    )