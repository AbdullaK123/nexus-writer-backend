"""Repository classes — the only place raw SQL lives.

Repos take an asyncpg.Pool in the constructor and acquire connections per call.
This keeps them safe to share across requests and across background tasks.

Methods return Pydantic models (see src/data/schemas) — never raw `Record`s.
Service code never touches asyncpg or SQL.
"""
from src.data.repositories.scene import SceneRepository
from src.data.repositories.user import UserRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.story import StoryRepository
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.chat import ChatRepository

__all__ = [
    "SceneRepository",
    "UserRepository",
    "SessionRepository",
    "StoryRepository",
    "ChapterRepository",
    "ChatRepository"
]
