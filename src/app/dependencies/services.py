from functools import lru_cache

from fastapi import Depends, Request
from loguru import logger

from src.app.dependencies.repositories import (
    get_chapter_repository,
    get_scene_repository,
    get_session_repository,
    get_story_repository,
    get_user_repository,
)
from src.data.repositories import (
    ChapterRepository,
    SceneRepository,
    SessionRepository,
    StoryRepository,
    UserRepository,
)
from src.infrastructure.ai import OpenAIProvider, AIProvider
from src.infrastructure.config.settings import config
from src.infrastructure.db.pool import init_pool, close_pool
from src.service.auth import AuthService
from src.service.chapter import ChapterService
from src.service.extraction import ExtractionService
from src.service.story import StoryService


async def init_infrastructure() -> None:
    await init_pool()
    logger.info("infra.db.connected")


async def shutdown_infrastructure() -> None:
    await close_pool()
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


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> AuthService:
    return AuthService(user_repo, session_repo)


def get_story_service(
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
    provider: AIProvider = Depends(get_ai_provider),
) -> StoryService:
    return StoryService(story_repo, chapter_repo, scene_repo, provider, config.search)


def get_chapter_service(
    story_repo: StoryRepository = Depends(get_story_repository),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
) -> ChapterService:
    return ChapterService(story_repo, chapter_repo, scene_repo)


def get_extraction_service(
    provider: AIProvider = Depends(get_ai_provider),
    chapter_repo: ChapterRepository = Depends(get_chapter_repository),
    scene_repo: SceneRepository = Depends(get_scene_repository),
) -> ExtractionService:
    return ExtractionService(provider, chapter_repo, scene_repo)