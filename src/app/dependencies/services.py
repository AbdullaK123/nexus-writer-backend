from functools import lru_cache

from fastapi import Depends, Request
from loguru import logger
from pydantic_ai import Agent
import redis.asyncio as aioredis
from src.app.dependencies.redis import get_redis
from src.app.dependencies.repositories import (
    get_analytics_repository,
    get_chapter_repository,
    get_chat_repository,
    get_scene_repository,
    get_session_repository,
    get_story_repository,
    get_user_repository,
)
from src.data.repositories import (
    ChapterRepository,
    ChatRepository,
    SceneRepository,
    SessionRepository,
    StoryRepository,
    UserRepository,
)
from src.data.repositories.analytics import AnalyticsRepository
from src.infrastructure.ai import OpenAIProvider, AIProvider
from src.infrastructure.config.settings import config
from src.infrastructure.db.pool import init_pool as init_db_pool, close_pool as close_db_pool
from src.infrastructure.redis.pool import init_pool as init_redis_pool, close_pool as close_redis_pool
from src.service.analytics.service import AnalyticsService
from src.service.auth import AuthService
from src.service.chapter import ChapterService
from src.service.chat import ChatService
from src.service.chat.agent import ChatDeps, build_agent
from src.service.extraction import ExtractionService
from src.service.story import StoryService
# from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor


async def init_infrastructure() -> None:
    # AsyncPGInstrumentor().instrument()
    await init_db_pool()
    init_redis_pool()
    logger.info("infra.db.connected")


async def shutdown_infrastructure() -> None:
    await close_db_pool()
    await close_redis_pool()
    logger.info("infra.db.disconnected")


@lru_cache
def build_ai_provider() -> AIProvider:
    """Construct the singleton AI provider. Cached so repeated calls (lifespan,
    tests, scripts) share one client + concurrency semaphore."""
    return OpenAIProvider()


def get_ai_provider(request: Request) -> AIProvider:
    """FastAPI dependency. Reads the provider from app.state, where lifespan
    stashed it at startup. Override in tests via app.dependency_overrides."""
    return request.app.state.ai_provider


@lru_cache
def build_chat_agent() -> Agent[ChatDeps, str]:
    """Construct the singleton pydantic-ai chat agent. The agent itself is
    stateless (deps are passed per-run) and registers tools at construction
    time, so building it once is correct."""
    return build_agent(config.ai.default_model)


def get_chat_agent(request: Request) -> Agent[ChatDeps, str]:
    """FastAPI dependency. Reads the agent from app.state, where lifespan
    stashed it at startup."""
    return request.app.state.chat_agent


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> AuthService:
    return AuthService(user_repo, session_repo)


def get_analytics_service(
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
    provider: AIProvider = Depends(get_ai_provider),
    redis: aioredis.Redis = Depends(get_redis)
) -> AnalyticsService:
    return AnalyticsService(
        analytics_repo=analytics_repo,
        story_repo=story_repo,
        chapter_repo=chapter_repo,
        scene_repo=scene_repo,
        provider=provider,
        redis=redis
    )


def get_story_service(
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
    provider: AIProvider = Depends(get_ai_provider),
    redis: aioredis.Redis = Depends(get_redis)
) -> StoryService:
    return StoryService(story_repo, chapter_repo, scene_repo, provider, config.search, redis)


def get_chapter_service(
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
    provider: AIProvider = Depends(get_ai_provider),
    redis: aioredis.Redis = Depends(get_redis)
) -> ChapterService:
    return ChapterService(story_repo, chapter_repo, scene_repo, provider, redis)


def get_extraction_service(
    provider: AIProvider = Depends(get_ai_provider),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
) -> ExtractionService:
    return ExtractionService(provider, chapter_repo, scene_repo)


def get_chat_service(
    provider: AIProvider = Depends(get_ai_provider),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_service: ChapterService = Depends(get_chapter_service),
    story_service: StoryService = Depends(get_story_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    agent: Agent[ChatDeps, str] = Depends(get_chat_agent),
) -> ChatService:
    return ChatService(
        provider=provider,
        chat_repo=chat_repo,
        story_repo=story_repo,
        chapter_service=chapter_service,
        story_service=story_service,
        analytics_service=analytics_service,
        agent=agent,
    )