from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from yoyo import get_backend, read_migrations

from src.data.repositories.chat import ChatRepository
from src.data.repositories.session import SessionRepository
from src.data.schemas.auth import SessionRow, UserRow
from src.data.schemas.chat import ChatThreadRow
from src.data.schemas.story import StoryRow
from src.infrastructure.db.pool import _setup_connection
from tests.data.factories import make_story, make_user


@pytest.fixture(scope="session")
def run_migrations(postgres_url: str):
    backend = get_backend(postgres_url)
    migrations = read_migrations("migrations/yoyo")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


@pytest_asyncio.fixture
async def db_pool(
    run_migrations,
    postgres_url: str,
) -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(
        postgres_url,
        min_size=1,
        max_size=5,
        init=_setup_connection,
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def clean_db(db_pool: asyncpg.Pool) -> AsyncIterator[asyncpg.Pool]:
    yield db_pool
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            TRUNCATE
                "user", story, chapter, scene,
                session, chat_thread, chat_message
            CASCADE
            """
        )


@pytest.fixture
def chat_repo(clean_db: asyncpg.Pool) -> ChatRepository:
    return ChatRepository(clean_db)


@pytest.fixture
def session_repo(clean_db: asyncpg.Pool) -> SessionRepository:
    return SessionRepository(clean_db)


@pytest_asyncio.fixture
async def repo_user(clean_db: asyncpg.Pool) -> UserRow:
    return await make_user(clean_db)


@pytest_asyncio.fixture
async def repo_other_user(clean_db: asyncpg.Pool) -> UserRow:
    return await make_user(clean_db)


@pytest_asyncio.fixture
async def repo_story(clean_db: asyncpg.Pool, repo_user: UserRow) -> StoryRow:
    return await make_story(clean_db, user_id=repo_user.id)


@pytest_asyncio.fixture
async def repo_chat_thread(
    chat_repo: ChatRepository,
    repo_user: UserRow,
    repo_story: StoryRow,
) -> ChatThreadRow:
    return await chat_repo.create_thread(repo_user.id, repo_story.id, "Thread")


@pytest_asyncio.fixture
async def valid_session(
    session_repo: SessionRepository,
    repo_user: UserRow,
) -> SessionRow:
    return await session_repo.create(
        session_id="valid-session",
        user_id=repo_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )


@pytest_asyncio.fixture
async def expired_session(
    session_repo: SessionRepository,
    repo_user: UserRow,
) -> SessionRow:
    return await session_repo.create(
        session_id="expired-session",
        user_id=repo_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
