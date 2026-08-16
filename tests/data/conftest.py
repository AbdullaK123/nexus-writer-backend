from yoyo import get_backend, read_migrations
import pytest_asyncio
import asyncpg
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.story import StoryRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chapter import ChapterRow
from src.data.schemas.story import StoryRow
from src.infrastructure.db.pool import _setup_connection
from typing import AsyncIterator
from uuid_extensions import uuid7str
from lorem_text import lorem
import pytest
import random
from src.shared.utils.html import get_word_count


@pytest.fixture(scope="session")
def run_migrations(postgres_url: str):
    backend = get_backend(postgres_url)
    migrations = read_migrations("migrations/yoyo")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


# db bool
@pytest_asyncio.fixture
async def db_pool(
    run_migrations,
    postgres_url: str
) -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(
        postgres_url,
        min_size=1,
        max_size=5,
        init=_setup_connection
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def clean_db(
    db_pool: asyncpg.Pool
):
    yield db_pool
    async with db_pool.acquire() as conn:
        await conn.execute("""
            TRUNCATE
                "user", story, chapter, scene,
                session, chat_thread, chat_message
            CASCADE
        """)
    




