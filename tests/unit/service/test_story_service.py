"""Tests for StoryService — story CRUD + read endpoints.

Strategy: mock StoryRepository / ChapterRepository at the boundary and
construct a StoryService wrapping them.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.data.schemas.enums import StoryStatus
from src.data.schemas import StoryRow, ChapterRow
from src.data.schemas.story import (
    CreateStoryRequest,
    UpdateStoryRequest,
    StoryGridResponse,
    StoryDetailResponse,
)
from src.service.exceptions import ConflictError, NotFoundError
from src.service.story import StoryService


# ─── helpers ─────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _story(
    *,
    id: str = "s1",
    user_id: str = "u1",
    title: str = "Untitled",
    story_context: str | None = None,
    status: StoryStatus = StoryStatus.ONGOING,
    path_array: list[str] | None = None,
) -> StoryRow:
    return StoryRow(
        id=id,
        user_id=user_id,
        title=title,
        story_context=story_context,
        status=status,
        path_array=path_array,
        created_at=_now(),
        updated_at=_now(),
    )


def _chapter(
    *,
    id: str = "c1",
    story_id: str = "s1",
    user_id: str = "u1",
    title: str = "Ch",
    word_count: int = 0,
    created_at: datetime | None = None,
) -> ChapterRow:
    return ChapterRow(
        id=id,
        story_id=story_id,
        user_id=user_id,
        title=title,
        content="<p></p>",
        published=False,
        word_count=word_count,
        next_chapter_id=None,
        prev_chapter_id=None,
        created_at=created_at or _now(),
        updated_at=_now(),
    )


def _story_repo_mock():
    repo = MagicMock(name="StoryRepository")
    repo.exists_with_title = AsyncMock(return_value=False)
    repo.create = AsyncMock(return_value=_story())
    repo.update = AsyncMock(return_value=_story())
    repo.delete = AsyncMock(return_value=True)
    repo.get = AsyncMock(return_value=None)
    repo.list_for_user = AsyncMock(return_value=[])
    return repo


def _chapter_repo_mock():
    repo = MagicMock(name="ChapterRepository")
    repo.list_by_story = AsyncMock(return_value=[])
    repo.list_by_story_ids = AsyncMock(return_value=[])
    return repo


def _service(story_repo=None, chapter_repo=None) -> StoryService:
    return StoryService(
        story_repo or _story_repo_mock(),
        chapter_repo or _chapter_repo_mock(),
    )


# ─── create ──────────────────────────────────────────────────────────────────


class TestCreate:
    async def test_creates_when_title_unique(self):
        repo = _story_repo_mock()
        svc = _service(story_repo=repo)
        result = await svc.create_story("u1", CreateStoryRequest(title="A New Story"))
        assert result == {"message": "Story successfully created"}
        repo.create.assert_awaited_once_with(user_id="u1", title="A New Story")

    async def test_raises_conflict_when_user_already_has_story_with_same_title(self):
        repo = _story_repo_mock()
        repo.exists_with_title = AsyncMock(return_value=True)
        svc = _service(story_repo=repo)
        with pytest.raises(ConflictError):
            await svc.create_story("u1", CreateStoryRequest(title="Dup"))

    async def test_does_not_create_row_on_conflict(self):
        repo = _story_repo_mock()
        repo.exists_with_title = AsyncMock(return_value=True)
        svc = _service(story_repo=repo)
        with pytest.raises(ConflictError):
            await svc.create_story("u1", CreateStoryRequest(title="Dup"))
        repo.create.assert_not_awaited()


# ─── update ──────────────────────────────────────────────────────────────────


class TestUpdate:
    async def test_raises_not_found_when_story_doesnt_belong_to_user(self):
        repo = _story_repo_mock()
        repo.update = AsyncMock(return_value=None)
        svc = _service(story_repo=repo)
        with pytest.raises(NotFoundError):
            await svc.update_story("u1", "s1", UpdateStoryRequest(title="New"))

    async def test_only_explicitly_set_fields_are_updated(self):
        repo = _story_repo_mock()
        svc = _service(story_repo=repo)
        await svc.update_story("u1", "s1", UpdateStoryRequest(title="New"))
        repo.update.assert_awaited_once_with(
            story_id="s1", user_id="u1", fields={"title": "New"},
        )

    async def test_unset_fields_excluded(self):
        repo = _story_repo_mock()
        svc = _service(story_repo=repo)
        await svc.update_story("u1", "s1", UpdateStoryRequest())
        repo.update.assert_awaited_once_with(
            story_id="s1", user_id="u1", fields={},
        )


# ─── delete ──────────────────────────────────────────────────────────────────


class TestDelete:
    async def test_raises_not_found_when_story_belongs_to_someone_else(self):
        repo = _story_repo_mock()
        repo.delete = AsyncMock(return_value=False)
        svc = _service(story_repo=repo)
        with pytest.raises(NotFoundError):
            await svc.delete_story("u1", "s1")

    async def test_returns_success_message_on_delete(self):
        repo = _story_repo_mock()
        svc = _service(story_repo=repo)
        result = await svc.delete_story("u1", "s1")
        assert result == {"message": "Story successfully deleted"}
        repo.delete.assert_awaited_once_with(story_id="s1", user_id="u1")


# ─── get_story_details ───────────────────────────────────────────────────────


class TestGetStoryDetails:
    async def test_raises_not_found_when_story_missing(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=None)
        svc = _service(story_repo=story_repo)
        with pytest.raises(NotFoundError):
            await svc.get_story_details("u1", "missing")

    async def test_returns_details_with_zero_chapters(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story())
        svc = _service(story_repo=story_repo)

        result = await svc.get_story_details("u1", "s1")

        assert isinstance(result, StoryDetailResponse)
        assert result.total_chapters == 0
        assert result.word_count == 0
        assert result.chapters == []

    async def test_word_count_aggregates_chapter_word_counts(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story(path_array=["a", "b"]))
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(return_value=[
            _chapter(id="a", word_count=100),
            _chapter(id="b", word_count=250),
        ])
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_details("u1", "s1")
        assert result.word_count == 350
        assert result.total_chapters == 2

    async def test_orders_chapters_by_path_array(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story(path_array=["b", "a", "c"]))
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(return_value=[
            _chapter(id="a"), _chapter(id="b"), _chapter(id="c"),
        ])
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_details("u1", "s1")
        assert [c.id for c in result.chapters] == ["b", "a", "c"]

    async def test_skips_path_entries_with_no_matching_chapter(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "ghost", "b"]),
        )
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(return_value=[
            _chapter(id="a"), _chapter(id="b"),
        ])
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_details("u1", "s1")
        assert [c.id for c in result.chapters] == ["a", "b"]


# ─── get_all_stories ─────────────────────────────────────────────────────────


class TestGetAllStories:
    async def test_returns_empty_grid_when_user_has_no_stories(self):
        svc = _service()
        result = await svc.get_all_stories("u1")
        assert result == StoryGridResponse(stories=[])

    async def test_groups_chapters_by_story_for_word_count(self):
        story_repo = _story_repo_mock()
        story_repo.list_for_user = AsyncMock(return_value=[
            _story(id="s1", title="A"),
            _story(id="s2", title="B"),
        ])
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story_ids = AsyncMock(return_value=[
            _chapter(id="c1", story_id="s1", word_count=100),
            _chapter(id="c2", story_id="s1", word_count=50),
            _chapter(id="c3", story_id="s2", word_count=200),
        ])
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_all_stories("u1")
        by_id = {s.id: s for s in result.stories}
        assert by_id["s1"].word_count == 150
        assert by_id["s1"].total_chapters == 2
        assert by_id["s2"].word_count == 200
        assert by_id["s2"].total_chapters == 1
