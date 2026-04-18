from fastapi import Depends
from tortoise import Tortoise

from src.infrastructure.db.postgres import TORTOISE_ORM
from src.shared.utils.decorators import singleton

from src.service.auth.service import AuthService
from src.service.target.service import TargetService
from src.service.chapter.service import ChapterService
from src.service.story.service import StoryService
from src.infrastructure.ai import AIProvider, OpenAIProvider
from src.infrastructure.config import config


# ── Infrastructure lifecycle ─────────────────────────────────────────

async def init_infrastructure() -> None:
    await Tortoise.init(config=TORTOISE_ORM)


async def shutdown_infrastructure() -> None:
    await Tortoise.close_connections()


# ── Service dependencies ────────────────────────────────────────────

def get_auth_service() -> AuthService:
    return singleton(AuthService)()

def get_ai_provider(model: str = config.ai.default_model) -> AIProvider:
    # later we'll have support for more than just open ai
    return singleton(OpenAIProvider)()


def get_target_service() -> TargetService:
    return singleton(TargetService)()


def get_chapter_service() -> ChapterService:
    return singleton(ChapterService)()


def get_story_service(
    target_service: TargetService = Depends(get_target_service),
) -> StoryService:
    return singleton(StoryService)(target_service=target_service)
