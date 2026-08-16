
# user factory
import random

import asyncpg
from lorem_text import lorem
from uuid_extensions import uuid7str
from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.story import StoryRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chapter import ChapterRow
from src.data.schemas.story import StoryRow
from src.shared.utils.html import get_word_count


async def make_user(
    pool: asyncpg.Pool
) -> UserRow:
    repo = UserRepository(pool)
    return await repo.create(
        username=f"testuser_{uuid7str()}",
        email=f"testemail_{uuid7str()}@example.com",
        password_hash="hashed_password",
        profile_img=None
    )
    

# story factory
async def make_story(
    pool: asyncpg.Pool,
    *,
    user_id: str
) -> StoryRow:
    repo = StoryRepository(pool)
    return await repo.create(
        user_id=user_id,
        title=f"test_story_{uuid7str()}"
    )


# chapter factory
async def make_chapter(
    pool: asyncpg.Pool,
    *,
    user_id: str,
    story_id: str
) -> ChapterRow:
    repo = ChapterRepository(pool)

    chapter_title = lorem.words(10)
    raw_chapter_text = lorem.paragraphs(5)
    chapter_text = "\n".join([
        f"<p>{line}</p>"
        for line in raw_chapter_text.split("\n")
    ])

    return await repo.create(
        story_id=story_id,
        user_id=user_id,
        title=chapter_title,
        content=chapter_text,
        word_count=get_word_count(chapter_text)
    )


# scene factory
async def make_scene(
    pool: asyncpg.Pool,
    *,
    chapter_id: str,
    story_id: str,
    user_id: str,
    position: int = 0
) -> dict:

    sql = """
    INSERT INTO scene
            (id, chapter_id, story_id, user_id, position,
             title, start_quote, end_quote, description,
             tension, pacing, pov, mentioned_entities, tags,
             questions_raised, created_at, updated_at)
        VALUES
            ($1, $2, $3, $4, $5,
             $6, $7, $8, $9,
             $10, $11, $12, $13, $14,
             $15, NOW(), NOW())
        RETURNING *
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            sql,
            uuid7str(),
            chapter_id,
            story_id,
            user_id,
            position,
            lorem.words(10),
            lorem.words(10),
            lorem.words(10),
            lorem.paragraphs(1),
            random.choice(["low", "medium", "high"]),
            random.choice(["slow", "steady", "fast"]),
            lorem.words(2),
            [lorem.words(2) for _ in range(3)],
            [lorem.words(2) for _ in range(5)],
            [lorem.words(4) for _ in range(4)]
        )

    return dict(row)
