# tests/service/conftest.py

from typing import Any, cast

import pytest
import pytest_asyncio
from lorem_text import lorem
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from src.data.schemas.auth import RegistrationData, UserResponse
from src.data.schemas.chapter import ChapterRow
from src.data.schemas.chat import ChatThreadRow, ConversationTurnRequest
from src.data.schemas.story import StoryRow
from src.infrastructure.config.settings import SearchConfig
from src.service.analytics.service import AnalyticsService
from src.service.auth.service import AuthService
from src.service.chapter.service import ChapterService
from src.service.chat.service import ChatService
from src.service.embedding.service import EmbeddingService
from src.service.extraction.service import ExtractionService
from src.service.story.service import StoryService
from tests.service.mocks import (
    FakeAIProvider,
    FakeAnalyticsRepository,
    FakeChapterRepository,
    FakeChatAgent,
    FakeChatRepository,
    FakePubSub,
    FakeQueue,
    FakeRedis,
    FakeSceneRepository,
    FakeSessionRepository,
    FakeStoryRepository,
    FakeUserRepository,
)
from tests.service.mocks.extraction import (
    ExtractionChapterRepository,
    ExtractionSceneRepository,
    RecordingLogger,
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
def fake_chat_agent() -> FakeChatAgent:
    return FakeChatAgent()


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
def extraction_context():
    chapter_repo = ExtractionChapterRepository()
    scene_repo = ExtractionSceneRepository(chapter_repo)
    provider = FakeAIProvider()
    service = ExtractionService(
        provider=provider,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo,
    )
    return service, provider, chapter_repo, scene_repo


@pytest.fixture
def recording_logger() -> RecordingLogger:
    return RecordingLogger()


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


@pytest.fixture
def chat_service(
    fake_provider: FakeAIProvider,
    fake_chat_repo: FakeChatRepository,
    fake_story_repo: FakeStoryRepository,
    chapter_service: ChapterService,
    story_service: StoryService,
    analytics_service: AnalyticsService,
    fake_chat_agent: FakeChatAgent,
) -> ChatService:
    return ChatService(
        provider=cast(Any, fake_provider),
        chat_repo=cast(Any, fake_chat_repo),
        story_repo=cast(Any, fake_story_repo),
        chapter_service=chapter_service,
        story_service=story_service,
        analytics_service=analytics_service,
        agent=cast(Any, fake_chat_agent),
    )


# ── Domain data fixtures ─────────────────────────────

@pytest_asyncio.fixture
async def test_user(auth_service: AuthService) -> UserResponse:
    return await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="testuser@email.com",
            password="mypassword123@ABC",
        )
    )


@pytest_asyncio.fixture
async def test_story(
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
) -> StoryRow:
    return await fake_story_repo.create(user_id=test_user.id, title="Test")


@pytest_asyncio.fixture
async def other_story(
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
) -> StoryRow:
    return await fake_story_repo.create(user_id=test_user.id, title="Other Story")


@pytest_asyncio.fixture
async def test_chapter(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository,
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title="test",
        content="test content",
        word_count=2,
    )


@pytest_asyncio.fixture
async def chapter_with_enough_content(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository,
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title=lorem.words(10),
        content=lorem.words(1100),
        word_count=1100,
    )


@pytest_asyncio.fixture
async def chapter_with_not_enough_content(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository,
) -> ChapterRow:
    return await fake_chapter_repo.create(
        story_id=test_story.id,
        user_id=test_user.id,
        title=lorem.words(10),
        content=lorem.words(900),
        word_count=900,
    )


@pytest_asyncio.fixture
async def published_chapter_with_enough_content(
    chapter_with_enough_content: ChapterRow,
    fake_chapter_repo: FakeChapterRepository,
) -> ChapterRow:
    updated = await fake_chapter_repo.update(
        chapter_id=chapter_with_enough_content.id,
        user_id=chapter_with_enough_content.user_id,
        fields={"published": True},
    )
    if updated is None:
        raise RuntimeError("Misconfigured fixture. Published chapter can not be None")
    return updated


@pytest_asyncio.fixture
async def chat_thread(
    test_user: UserResponse,
    test_story: StoryRow,
    fake_chat_repo: FakeChatRepository,
) -> ChatThreadRow:
    return await fake_chat_repo.create_thread(
        test_user.id,
        test_story.id,
        "Test Thread",
    )


@pytest.fixture
def conversation_turn(
    test_story: StoryRow,
    chat_thread: ChatThreadRow,
) -> ConversationTurnRequest:
    return ConversationTurnRequest(
        story_id=test_story.id,
        thread_id=chat_thread.id,
        user_message="What happens next?",
    )


@pytest.fixture
def chat_history_messages() -> list[ModelMessage]:
    return [
        ModelRequest(parts=[UserPromptPart(content="What happened before?")]),
        ModelResponse(parts=[TextPart(content="The gate opened.")]),
    ]


@pytest.fixture
def chat_new_messages() -> list[ModelMessage]:
    return [
        ModelRequest(parts=[UserPromptPart(content="What happens next?")]),
        ModelResponse(parts=[TextPart(content="The council meets.")]),
    ]


@pytest_asyncio.fixture
async def seeded_chat_history(
    test_user: UserResponse,
    chat_thread: ChatThreadRow,
    fake_chat_repo: FakeChatRepository,
    chat_history_messages: list[ModelMessage],
) -> list[ModelMessage]:
    serialized = ModelMessagesTypeAdapter.dump_python(chat_history_messages, mode="json")
    for message, dumped in zip(chat_history_messages, serialized, strict=True):
        await fake_chat_repo.append_message(
            thread_id=chat_thread.id,
            user_id=test_user.id,
            kind=message.kind,
            message=dumped,
        )
    return chat_history_messages


@pytest.fixture
def fake_queue(monkeypatch: pytest.MonkeyPatch) -> FakeQueue:
    queue = FakeQueue()
    monkeypatch.setattr("src.service.chapter.service.queue", queue)
    return queue


@pytest.fixture
async def clear_cache(fake_redis: FakeRedis):
    yield
    await fake_redis.flush()
