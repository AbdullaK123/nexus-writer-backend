import asyncio

import asyncpg
from uuid_extensions import uuid7str

from src.data.repositories.story import StoryRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.story import StoryRow


async def test_concurrent_path_appends_do_not_lose_chapters(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    repo_story: StoryRow,
) -> None:
    """Two transactions reading the same path must not overwrite each other's append."""
    repo = StoryRepository(clean_db)
    chapter_a = uuid7str()
    chapter_b = uuid7str()

    ready = asyncio.Event()
    waiting = 0
    waiting_lock = asyncio.Lock()

    async def append(chapter_id: str) -> None:
        nonlocal waiting
        async with clean_db.acquire() as conn:
            async with conn.transaction():
                path = await repo.get_path_array(repo_story.id, executor=conn)
                assert path is not None

                async with waiting_lock:
                    waiting += 1
                    if waiting == 2:
                        ready.set()
                await ready.wait()

                await repo.set_path_array(
                    repo_story.id,
                    [*path, chapter_id],
                    executor=conn,
                )

    await asyncio.gather(append(chapter_a), append(chapter_b))

    final_path = await repo.get_path_array(repo_story.id)

    assert final_path is not None
    assert len(final_path) == 2
    assert set(final_path) == {chapter_a, chapter_b}, (
        "story.path_array is a read-modify-write aggregate; concurrent chapter operations "
        "must not lose one transaction's update via last-writer-wins"
    )
