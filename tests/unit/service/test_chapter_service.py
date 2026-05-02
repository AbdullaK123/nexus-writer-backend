"""Tests for ChapterService — public methods + private path/pointer helpers.

Strategy: mock the three repos. Stub `chapter_repo.pool.acquire()` and
`conn.transaction()` to be async-context-manager no-ops so we can exercise
the transactional code paths. We're verifying that the service calls the
right repo methods with the right arguments — not that asyncpg actually
runs a transaction.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.data.schemas.enums import StoryStatus
from src.data.schemas import ChapterRow, StoryRow
from src.data.schemas.chapter import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterContentResponse,
    ChapterListResponse,
)
from src.service.chapter import ChapterService
from src.service.exceptions import NotFoundError, ValidationError, InternalError


# ─── helpers ─────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _story(
    *,
    id: str = "s1",
    user_id: str = "u1",
    title: str = "My Story",
    path_array: list[str] | None = None,
) -> StoryRow:
    return StoryRow(
        id=id, user_id=user_id, title=title, story_context=None,
        status=StoryStatus.ONGOING, path_array=path_array,
        created_at=_now(), updated_at=_now(),
    )


def _chapter(
    *,
    id: str = "ch1",
    story_id: str = "s1",
    user_id: str = "u1",
    title: str = "Ch",
    content: str = "<p>hello world</p>",
    word_count: int = 2,
) -> ChapterRow:
    return ChapterRow(
        id=id, story_id=story_id, user_id=user_id, title=title,
        content=content, published=False, word_count=word_count,
        next_chapter_id=None, prev_chapter_id=None,
        created_at=_now(), updated_at=_now(),
    )


def _make_pool_mock():
    """Build a mock pool whose `.acquire()` and `conn.transaction()` are
    async context managers that hand back a sentinel connection."""
    conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _txn():
        yield None
    conn.transaction = MagicMock(side_effect=_txn)

    @asynccontextmanager
    async def _acquire():
        yield conn
    pool = MagicMock(name="pool")
    pool.acquire = MagicMock(side_effect=_acquire)
    return pool


def _story_repo_mock(*, path: list[str] | None = None):
    repo = MagicMock(name="StoryRepository")
    repo.get = AsyncMock(return_value=None)
    repo.get_path_array = AsyncMock(return_value=path)
    repo.set_path_array = AsyncMock(return_value=None)
    repo.touch = AsyncMock(return_value=None)
    repo.pool = _make_pool_mock()
    return repo


def _chapter_repo_mock():
    repo = MagicMock(name="ChapterRepository")
    repo.get_with_story_title = AsyncMock(return_value=None)
    repo.list_by_story = AsyncMock(return_value=[])
    repo.create = AsyncMock(return_value=_chapter())
    repo.update = AsyncMock(return_value=_chapter())
    repo.delete = AsyncMock(return_value="s1")
    repo.sync_pointers = AsyncMock(return_value=None)
    repo.pool = _make_pool_mock()
    return repo


def _scene_repo_mock():
    repo = MagicMock(name="SceneRepository")
    repo.list_by_chapter = AsyncMock(return_value=[])
    repo.mark_chapter_stale = AsyncMock(return_value=None)
    return repo


def _service(story_repo=None, chapter_repo=None, scene_repo=None) -> ChapterService:
    return ChapterService(
        story_repo or _story_repo_mock(),
        chapter_repo or _chapter_repo_mock(),
        scene_repo or _scene_repo_mock(),
    )


# ─── get_chapter_with_navigation ─────────────────────────────────────────────


class TestGetChapterWithNavigation:
    async def test_raises_not_found_when_chapter_missing(self):
        svc = _service()
        with pytest.raises(NotFoundError):
            await svc.get_chapter_with_navigation("missing", "u1")

    async def test_returns_full_html_when_as_html_true(self):
        chapter_repo = _chapter_repo_mock()
        ch = _chapter(content="<p>Once upon a time</p>")
        chapter_repo.get_with_story_title = AsyncMock(
            return_value=(ch, "My Story"),
        )
        svc = _service(chapter_repo=chapter_repo)

        result = await svc.get_chapter_with_navigation("ch1", "u1", as_html=True)
        assert isinstance(result, ChapterContentResponse)
        assert result.content == "<p>Once upon a time</p>"


# ─── get_story_chapters ──────────────────────────────────────────────────────


class TestGetStoryChapters:
    async def test_raises_not_found_when_story_belongs_to_other_user(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=None)
        svc = _service(story_repo=story_repo)
        with pytest.raises(NotFoundError):
            await svc.get_story_chapters("s1", "u1")

    async def test_returns_empty_list_when_no_chapters_exist(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story(path_array=[]))
        svc = _service(story_repo=story_repo)

        result = await svc.get_story_chapters("s1", "u1")
        assert isinstance(result, ChapterListResponse)
        assert result.chapters == []

    async def test_returns_empty_list_when_path_array_empty(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story(path_array=None))
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(
            return_value=[_chapter(id="a"), _chapter(id="b")],
        )
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_chapters("s1", "u1")
        assert result.chapters == []

    async def test_orders_chapters_by_path_array_not_creation_time(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["b", "a", "c"]),
        )
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(return_value=[
            _chapter(id="a"), _chapter(id="b"), _chapter(id="c"),
        ])
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_chapters("s1", "u1")
        assert [c.id for c in result.chapters] == ["b", "a", "c"]

    async def test_skips_path_array_entries_with_no_matching_chapter(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "ghost", "b"]),
        )
        chapter_repo = _chapter_repo_mock()
        chapter_repo.list_by_story = AsyncMock(
            return_value=[_chapter(id="a"), _chapter(id="b")],
        )
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)

        result = await svc.get_story_chapters("s1", "u1")
        assert [c.id for c in result.chapters] == ["a", "b"]


# ─── create_chapter ──────────────────────────────────────────────────────────


class TestCreateChapter:
    async def test_raises_not_found_when_story_missing(self):
        svc = _service()
        with pytest.raises(NotFoundError):
            await svc.create_chapter(
                "s1", "u1",
                CreateChapterRequest(title="T", content="<p>x</p>"),
            )

    async def test_creates_chapter_and_invokes_orchestration(self, mocker):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story())
        chapter_repo = _chapter_repo_mock()
        new_ch = _chapter(id="new-ch")
        chapter_repo.create = AsyncMock(return_value=new_ch)
        chapter_repo.get_with_story_title = AsyncMock(
            return_value=(new_ch, "My Story"),
        )
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)
        spy = mocker.patch.object(
            svc, "_handle_chapter_creation", new=AsyncMock(),
        )

        result = await svc.create_chapter(
            "s1", "u1",
            CreateChapterRequest(title="New", content="<p>hello</p>"),
        )
        assert isinstance(result, ChapterContentResponse)
        chapter_repo.create.assert_awaited_once()
        spy.assert_awaited_once()


# ─── update_chapter ──────────────────────────────────────────────────────────


class TestUpdateChapter:
    async def test_raises_not_found_when_chapter_missing(self):
        svc = _service()
        with pytest.raises(NotFoundError):
            await svc.update_chapter(
                "missing", "u1", UpdateChapterRequest(title="X"),
            )

    async def test_updates_word_count_when_content_changes(self):
        chapter_repo = _chapter_repo_mock()
        ch = _chapter()
        chapter_repo.get_with_story_title = AsyncMock(
            return_value=(ch, "My Story"),
        )
        chapter_repo.update = AsyncMock(return_value=ch)
        svc = _service(chapter_repo=chapter_repo)

        await svc.update_chapter(
            "ch1", "u1",
            UpdateChapterRequest(content="<p>one two three four</p>"),
        )
        call_kwargs = chapter_repo.update.await_args.kwargs
        assert "word_count" in call_kwargs["fields"]
        assert call_kwargs["fields"]["word_count"] == 4


# ─── delete_chapter ──────────────────────────────────────────────────────────


class TestDeleteChapter:
    async def test_raises_not_found_when_chapter_missing(self):
        chapter_repo = _chapter_repo_mock()
        chapter_repo.delete = AsyncMock(return_value=None)
        svc = _service(chapter_repo=chapter_repo)
        with pytest.raises(NotFoundError):
            await svc.delete_chapter("ch1", "u1")

    async def test_invokes_deletion_handler_with_returned_story_id(self, mocker):
        chapter_repo = _chapter_repo_mock()
        chapter_repo.delete = AsyncMock(return_value="s1")
        svc = _service(chapter_repo=chapter_repo)
        spy = mocker.patch.object(
            svc, "_handle_chapter_deletion", new=AsyncMock(),
        )

        result = await svc.delete_chapter("ch1", "u1")
        assert result == {"message": "Chapter was successfully deleted"}
        spy.assert_awaited_once()


# ─── reorder_chapters ────────────────────────────────────────────────────────


class TestReorderChapters:
    async def test_raises_not_found_when_story_belongs_to_other_user(self):
        svc = _service()
        with pytest.raises(NotFoundError):
            await svc.reorder_chapters(
                "s1", "u1", ReorderChapterRequest(from_pos=0, to_pos=1),
            )

    async def test_raises_validation_when_path_array_empty(self):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(return_value=_story(path_array=[]))
        svc = _service(story_repo=story_repo)
        with pytest.raises(ValidationError):
            await svc.reorder_chapters(
                "s1", "u1", ReorderChapterRequest(from_pos=0, to_pos=0),
            )

    @pytest.mark.parametrize("from_pos", [-1, 5])
    async def test_raises_validation_when_from_pos_out_of_bounds(self, from_pos):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "b", "c"]),
        )
        svc = _service(story_repo=story_repo)
        with pytest.raises(ValidationError):
            await svc.reorder_chapters(
                "s1", "u1",
                ReorderChapterRequest(from_pos=from_pos, to_pos=0),
            )

    @pytest.mark.parametrize("to_pos", [-1, 5])
    async def test_raises_validation_when_to_pos_out_of_bounds(self, to_pos):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "b", "c"]),
        )
        svc = _service(story_repo=story_repo)
        with pytest.raises(ValidationError):
            await svc.reorder_chapters(
                "s1", "u1",
                ReorderChapterRequest(from_pos=0, to_pos=to_pos),
            )

    async def test_no_op_when_from_equals_to_does_not_invoke_handler(self, mocker):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "b", "c"]),
        )
        svc = _service(story_repo=story_repo)
        spy = mocker.patch.object(
            svc, "_handle_chapter_reordering", new=AsyncMock(),
        )

        result = await svc.reorder_chapters(
            "s1", "u1", ReorderChapterRequest(from_pos=1, to_pos=1),
        )
        assert result == {"message": "No reordering needed"}
        spy.assert_not_awaited()

    async def test_invokes_handler_on_valid_reorder(self, mocker):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "b", "c"]),
        )
        svc = _service(story_repo=story_repo)
        spy = mocker.patch.object(
            svc, "_handle_chapter_reordering", new=AsyncMock(),
        )

        result = await svc.reorder_chapters(
            "s1", "u1", ReorderChapterRequest(from_pos=0, to_pos=2),
        )
        assert result == {"message": "Chapters reordered successfully"}
        spy.assert_awaited_once()

    async def test_wraps_handler_failure_in_internal_error(self, mocker):
        story_repo = _story_repo_mock()
        story_repo.get = AsyncMock(
            return_value=_story(path_array=["a", "b", "c"]),
        )
        svc = _service(story_repo=story_repo)
        mocker.patch.object(
            svc, "_handle_chapter_reordering",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        )

        with pytest.raises(InternalError):
            await svc.reorder_chapters(
                "s1", "u1", ReorderChapterRequest(from_pos=0, to_pos=2),
            )


# ─── path-array primitives (private) ─────────────────────────────────────────


class TestAppendChapterToPathEnd:
    async def test_raises_when_story_missing(self):
        svc = _service(story_repo=_story_repo_mock(path=None))
        with pytest.raises(ValueError, match="not found"):
            await svc._append_chapter_to_path_end("missing", "ch-1")

    async def test_appends_to_empty_path(self):
        story_repo = _story_repo_mock(path=[])
        svc = _service(story_repo=story_repo)
        await svc._append_chapter_to_path_end("s1", "ch-1")
        story_repo.set_path_array.assert_awaited_once_with(
            "s1", ["ch-1"], executor=None,
        )

    async def test_is_idempotent_when_chapter_already_in_path(self):
        story_repo = _story_repo_mock(path=["ch-1"])
        svc = _service(story_repo=story_repo)
        await svc._append_chapter_to_path_end("s1", "ch-1")
        story_repo.set_path_array.assert_not_awaited()

    async def test_appends_to_end_preserving_existing_order(self):
        story_repo = _story_repo_mock(path=["a", "b"])
        svc = _service(story_repo=story_repo)
        await svc._append_chapter_to_path_end("s1", "c")
        story_repo.set_path_array.assert_awaited_once_with(
            "s1", ["a", "b", "c"], executor=None,
        )

    async def test_passes_executor_through(self):
        story_repo = _story_repo_mock(path=[])
        svc = _service(story_repo=story_repo)
        sentinel = object()
        await svc._append_chapter_to_path_end("s1", "ch-1", conn=sentinel)
        story_repo.get_path_array.assert_awaited_once_with("s1", executor=sentinel)
        story_repo.set_path_array.assert_awaited_once_with(
            "s1", ["ch-1"], executor=sentinel,
        )


class TestRemoveChapterFromPath:
    async def test_no_op_when_story_missing(self):
        story_repo = _story_repo_mock(path=None)
        svc = _service(story_repo=story_repo)
        await svc._remove_chapter_from_path("missing", "ch")
        story_repo.set_path_array.assert_not_awaited()

    async def test_no_op_when_path_empty(self):
        story_repo = _story_repo_mock(path=[])
        svc = _service(story_repo=story_repo)
        await svc._remove_chapter_from_path("s1", "ch")
        story_repo.set_path_array.assert_not_awaited()

    async def test_no_op_when_chapter_not_in_path(self):
        story_repo = _story_repo_mock(path=["a", "b"])
        svc = _service(story_repo=story_repo)
        await svc._remove_chapter_from_path("s1", "ghost")
        story_repo.set_path_array.assert_not_awaited()

    async def test_removes_only_target_preserving_order(self):
        story_repo = _story_repo_mock(path=["a", "b", "c"])
        svc = _service(story_repo=story_repo)
        await svc._remove_chapter_from_path("s1", "b")
        story_repo.set_path_array.assert_awaited_once_with(
            "s1", ["a", "c"], executor=None,
        )


class TestReorderChapterPath:
    async def test_no_op_when_path_empty(self):
        story_repo = _story_repo_mock(path=[])
        svc = _service(story_repo=story_repo)
        await svc._reorder_chapter_path("s1", 0, 0)
        story_repo.set_path_array.assert_not_awaited()

    @pytest.mark.parametrize("from_pos,to_pos", [(-1, 0), (5, 0), (0, -1), (0, 5)])
    async def test_silent_on_out_of_bounds(self, from_pos, to_pos):
        story_repo = _story_repo_mock(path=["a", "b", "c"])
        svc = _service(story_repo=story_repo)
        await svc._reorder_chapter_path("s1", from_pos, to_pos)
        story_repo.set_path_array.assert_not_awaited()

    async def test_no_op_when_from_equals_to(self):
        story_repo = _story_repo_mock(path=["a", "b", "c"])
        svc = _service(story_repo=story_repo)
        await svc._reorder_chapter_path("s1", 1, 1)
        story_repo.set_path_array.assert_not_awaited()

    async def test_moves_via_pop_then_insert(self):
        story_repo = _story_repo_mock(path=["a", "b", "c", "d"])
        svc = _service(story_repo=story_repo)
        await svc._reorder_chapter_path("s1", 0, 2)
        story_repo.set_path_array.assert_awaited_once_with(
            "s1", ["b", "c", "a", "d"], executor=None,
        )


class TestSyncAllChapterPointers:
    async def test_no_op_when_story_missing(self):
        story_repo = _story_repo_mock(path=None)
        chapter_repo = _chapter_repo_mock()
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)
        await svc._sync_all_chapter_pointers("missing")
        chapter_repo.sync_pointers.assert_not_awaited()

    async def test_passes_path_to_chapter_repo(self):
        story_repo = _story_repo_mock(path=["a", "b"])
        chapter_repo = _chapter_repo_mock()
        svc = _service(story_repo=story_repo, chapter_repo=chapter_repo)
        await svc._sync_all_chapter_pointers("s1")
        chapter_repo.sync_pointers.assert_awaited_once_with(
            "s1", ["a", "b"], executor=None,
        )


class TestUpdateStoryTimestamp:
    async def test_delegates_to_repo_touch(self):
        story_repo = _story_repo_mock()
        svc = _service(story_repo=story_repo)
        await svc._update_story_timestamp("s1")
        story_repo.touch.assert_awaited_once_with("s1", executor=None)


# ─── orchestration ordering (private) ────────────────────────────────────────


def _track(order: list[str], label: str):
    async def _record(*_a, **_kw):
        order.append(label)
    return _record


class TestHandleChapterCreation:
    async def test_invokes_append_sync_and_timestamp_in_order(self, mocker):
        order: list[str] = []
        svc = _service()
        mocker.patch.object(
            svc, "_append_chapter_to_path_end", new=_track(order, "append"),
        )
        mocker.patch.object(
            svc, "_sync_all_chapter_pointers", new=_track(order, "sync"),
        )
        mocker.patch.object(
            svc, "_update_story_timestamp", new=_track(order, "ts"),
        )

        await svc._handle_chapter_creation("s1", "ch-1")
        assert order == ["append", "sync", "ts"]


class TestHandleChapterDeletion:
    async def test_invokes_remove_sync_and_timestamp_in_order(self, mocker):
        order: list[str] = []
        svc = _service()
        mocker.patch.object(
            svc, "_remove_chapter_from_path", new=_track(order, "remove"),
        )
        mocker.patch.object(
            svc, "_sync_all_chapter_pointers", new=_track(order, "sync"),
        )
        mocker.patch.object(
            svc, "_update_story_timestamp", new=_track(order, "ts"),
        )

        await svc._handle_chapter_deletion("s1", "ch-1")
        assert order == ["remove", "sync", "ts"]


class TestHandleChapterReordering:
    async def test_invokes_reorder_sync_and_timestamp_in_order(self, mocker):
        order: list[str] = []
        svc = _service()
        mocker.patch.object(
            svc, "_reorder_chapter_path", new=_track(order, "reorder"),
        )
        mocker.patch.object(
            svc, "_sync_all_chapter_pointers", new=_track(order, "sync"),
        )
        mocker.patch.object(
            svc, "_update_story_timestamp", new=_track(order, "ts"),
        )

        await svc._handle_chapter_reordering("s1", 0, 1)
        assert order == ["reorder", "sync", "ts"]
