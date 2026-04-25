from fastapi import Depends
from tortoise import Tortoise

from src.infrastructure.db.postgres import TORTOISE_ORM

from src.service.auth.service import AuthService
from src.service.target.service import TargetService
from src.service.chapter.service import ChapterService
from src.service.story.service import StoryService
from loguru import logger


# ── Infrastructure lifecycle ─────────────────────────────────────────


async def init_infrastructure() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("infra.db.connected")


async def shutdown_infrastructure() -> None:
    await Tortoise.close_connections()
    logger.info("infra.db.disconnected")


# ── Service dependencies ────────────────────────────────────────────


def get_auth_service() -> AuthService:
    return AuthService()


def get_target_service() -> TargetService:
    return TargetService()


def get_chapter_service() -> ChapterService:
    return ChapterService()


def get_story_service(
    target_service: TargetService = Depends(get_target_service),
) -> StoryService:
    return StoryService(target_service=target_service)
