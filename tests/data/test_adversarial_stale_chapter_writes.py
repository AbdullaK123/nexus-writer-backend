import asyncio
from typing import Any

import asyncpg

from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chapter import UpdateChapterRequest
from src.data.schemas.story import StoryRow
from src.service.chapter.service import ChapterService
from tests.data.factories import make_chapter


class DelayedChapterRepository(ChapterRepository):
    """Hold the first write after it enters the service's critical section."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        super().__init__(pool)
        self.first_update_entered = asyncio.Event()
        self.release_first_update = asyncio.Event()
        self.update_calls = 0

    async def update(
        self,
        *,
        chapter_id: str,
        user_id: str,
        fields: dict[str, Any],
        executor: Any | None = None,
    ):
        self.update_calls += 1
        if self.update_calls == 1:
            self.first_update_entered.set()
            await self.release_first_update.wait()

        return await super().update(
            chapter_id=chapter_id,
            user_id=user_id,
            fields=fields,
            executor=executor,
        )


async def test_concurrent_autosaves_are_serialized_at_service_boundary(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    repo_story: StoryRow,
) -> None:
    repo = DelayedChapterRepository(clean_db)
    story_repo = StoryRepository(clean_db)

    chapter = await make_chapter(
        clean_db,
        user_id=repo_user.id,
        story_id=repo_story.id,
    )
    await story_repo.append_chapter_to_path(repo_story.id, chapter.id)

    service = ChapterService(
        story_repo=story_repo,
        chapter_repo=repo,
        scene_repo=None,  # type: ignore[arg-type]
        analytics_repo=None,  # type: ignore[arg-type]
        provider=None,  # type: ignore[arg-type]
        redis=None,  # type: ignore[arg-type]
    )

    older = asyncio.create_task(
        service.update_chapter(
            chapter.id,
            repo_user.id,
            UpdateChapterRequest(content="STALE EDIT A"),
        )
    )

    # The older request is now inside the service's per-chapter write lock.
    await repo.first_update_entered.wait()

    newer = asyncio.create_task(
        service.update_chapter(
            chapter.id,
            repo_user.id,
            UpdateChapterRequest(content="NEWER EDIT B"),
        )
    )

    # Give the newer task a chance to run. It must not reach repository.update
    # while the first request still owns the chapter write lock.
    await asyncio.sleep(0)
    assert repo.update_calls == 1

    repo.release_first_update.set()
    await asyncio.gather(older, newer)

    persisted = await repo.get(chapter.id, repo_user.id)
    assert persisted is not None
    assert persisted.content == "NEWER EDIT B"
