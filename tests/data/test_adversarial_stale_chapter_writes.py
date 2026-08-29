import asyncio

import asyncpg

from src.data.repositories.chapter import ChapterRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.story import StoryRow
from tests.data.factories import make_chapter


async def test_delayed_older_autosave_cannot_overwrite_newer_edit(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    repo_story: StoryRow,
) -> None:
    repo = ChapterRepository(clean_db)
    chapter = await make_chapter(
        clean_db,
        user_id=repo_user.id,
        story_id=repo_story.id,
    )

    older_request_started = asyncio.Event()
    newer_request_committed = asyncio.Event()

    async def older_request() -> None:
        # Logical edit A starts first but is artificially delayed before SQL.
        async with clean_db.acquire() as conn:
            async with conn.transaction():
                older_request_started.set()
                await newer_request_committed.wait()
                await repo.update(
                    chapter_id=chapter.id,
                    user_id=repo_user.id,
                    fields={"content": "STALE EDIT A", "word_count": 3},
                    executor=conn,
                )

    async def newer_request() -> None:
        await older_request_started.wait()
        async with clean_db.acquire() as conn:
            async with conn.transaction():
                await repo.update(
                    chapter_id=chapter.id,
                    user_id=repo_user.id,
                    fields={"content": "NEWER EDIT B", "word_count": 3},
                    executor=conn,
                )
        newer_request_committed.set()

    await asyncio.gather(older_request(), newer_request())

    persisted = await repo.get(chapter.id, repo_user.id)
    assert persisted is not None
    assert persisted.content == "NEWER EDIT B", (
        "autosave requests can complete out of order; an older delayed request must not overwrite "
        "newer author text. Protect this with revision/CAS semantics or serialize writes before they "
        "reach an unconditional UPDATE."
    )
