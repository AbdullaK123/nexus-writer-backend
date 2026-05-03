"""FastAPI dependencies for repository instances.

Repos are constructed per-request from the app-state pool. They're stateless
w.r.t. connections (acquire from pool per call), so cheap to recreate and
safe to capture in BackgroundTasks closures.
"""
from fastapi import Depends
import asyncpg

from src.app.dependencies.db import get_db_pool
from src.data.repositories import (
    SceneRepository,
    UserRepository,
    SessionRepository,
    StoryRepository,
    ChapterRepository,
    ChatRepository,
)


def get_scene_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> SceneRepository:
    return SceneRepository(pool)


def get_user_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> UserRepository:
    return UserRepository(pool)


def get_session_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> SessionRepository:
    return SessionRepository(pool)


def get_story_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> StoryRepository:
    return StoryRepository(pool)


def get_chapter_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> ChapterRepository:
    return ChapterRepository(pool)


def get_chat_repository(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> ChatRepository:
    return ChatRepository(pool)
