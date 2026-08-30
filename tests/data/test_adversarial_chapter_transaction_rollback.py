from __future__ import annotations

import asyncpg
import pytest

from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chapter import CreateChapterRequest
from src.service.chapter.service import ChapterService
from src.service.exceptions import InternalError
from tests.service.mocks import FakeAIProvider, FakeRedis


def make_service(pool: asyncpg.Pool) -> tuple[ChapterService, StoryRepository, ChapterRepository]:
    story_repo = StoryRepository(pool)
    chapter_repo = ChapterRepository(pool)
    service = ChapterService(
        story_repo=story_repo,
        chapter_repo=chapter_repo,
        scene_repo=object(),  # unused by these hierarchy operations
        analytics_repo=object(),  # unused by these hierarchy operations
        provider=FakeAIProvider(),
        redis=FakeRedis(),
    )
    return service, story_repo, chapter_repo


@pytest.mark.asyncio
async def test_create_rolls_back_row_and_path_when_pointer_sync_fails(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    monkeypatch,
) -> None:
    service, story_repo, chapter_repo = make_service(clean_db)
    story = await story_repo.create(user_id=repo_user.id, title="Rollback Create")

    async def fail_sync(*args, **kwargs) -> None:
        raise RuntimeError("pointer sync exploded")

    monkeypatch.setattr(chapter_repo, "sync_pointers", fail_sync)

    with pytest.raises(InternalError):
        await service.create_chapter(
            story.id,
            repo_user.id,
            CreateChapterRequest(title="Must Roll Back"),
        )

    chapters = await chapter_repo.list_by_story(story.id, repo_user.id)
    path = await story_repo.get_path_array(story.id)

    assert chapters == [], (
        "a chapter row created inside a failed hierarchy transaction must not survive as an orphan"
    )
    assert path in (None, []), (
        "failed chapter creation must roll back the story path mutation as well as the chapter row"
    )


@pytest.mark.asyncio
async def test_delete_rolls_back_row_and_path_when_pointer_sync_fails(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    monkeypatch,
) -> None:
    service, story_repo, chapter_repo = make_service(clean_db)
    story = await story_repo.create(user_id=repo_user.id, title="Rollback Delete")
    chapter = await service.create_chapter(
        story.id,
        repo_user.id,
        CreateChapterRequest(title="Must Survive Failed Delete"),
    )
    original_path = await story_repo.get_path_array(story.id)
    assert original_path == [chapter.id]

    async def fail_sync(*args, **kwargs) -> None:
        raise RuntimeError("pointer sync exploded")

    monkeypatch.setattr(chapter_repo, "sync_pointers", fail_sync)

    with pytest.raises(RuntimeError, match="pointer sync exploded"):
        await service.delete_chapter(chapter.id, repo_user.id)

    stored = await chapter_repo.get(chapter.id, repo_user.id)
    path = await story_repo.get_path_array(story.id)

    assert stored is not None, (
        "a failed delete transaction must restore the chapter row; partial hierarchy deletion is data loss"
    )
    assert path == original_path, (
        "a failed delete must restore the exact canonical story path instead of leaving a dangling or missing chapter id"
    )
