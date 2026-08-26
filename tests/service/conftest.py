# tests/service/conftest.py

import pytest
import pytest_asyncio
from src.data.schemas.auth import RegistrationData, UserResponse
from src.data.schemas.chapter import ChapterRow
from src.data.schemas.story import StoryRow
from src.infrastructure.config.settings import SearchConfig
from src.service.story.service import StoryService
from src.service.chapter.service import ChapterService
from src.service.auth.service import AuthService
from src.service.extraction.service import ExtractionService
from src.service.embedding.service import EmbeddingService
from src.service.analytics.service import AnalyticsService
from lorem_text import lorem

from tests.service.mocks import (
    FakeQueue,
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
def fake_scene_repo(fake_chapter_repo: FakeChapterRepository) -> FakeSceneRepository:
    return FakeSceneRepository(fake_chapter_repo)


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


@pytest_asyncio.fixture
async def test_user(
    auth_service: AuthService
) -> UserResponse:
    return await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="testuser@email.com",
            password="mypassword123@ABC"
        )
    )

@pytest_asyncio.fixture
async def test_story(
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository
) -> StoryRow:
    return await fake_story_repo.create(user_id=test_user.id, title="Test")


@pytest_asyncio.fixture
async def test_chapter(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title="test",
        content="test content",
        word_count=2
    )

@pytest_asyncio.fixture
async def chapter_with_enough_content(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title=lorem.words(10),
        content=lorem.words(1100),
        word_count=1100
    )

@pytest_asyncio.fixture
async def chapter_with_not_enough_content(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title=lorem.words(10),
        content=lorem.words(900),
        word_count=900
    )

@pytest_asyncio.fixture
async def published_chapter_with_enough_content(
    chapter_with_enough_content: ChapterRow,
    fake_chapter_repo: FakeChapterRepository
) -> ChapterRow:
    updated =  await fake_chapter_repo.update(
        chapter_id=chapter_with_enough_content.id,
        user_id=chapter_with_enough_content.user_id,
        fields={
            "published": True
        }
    )
    if updated is None:
        raise RuntimeError("Misconfigured fixture. Published chapter can not be None")
    return updated


@pytest.fixture
def fake_queue(monkeypatch: pytest.MonkeyPatch) -> FakeQueue:
    fq = FakeQueue()
    monkeypatch.setattr("src.service.chapter.service.queue", fq)
    return fq

@pytest.fixture
async def clear_cache(
    fake_redis: FakeRedis
):
    yield
    await fake_redis.flush()