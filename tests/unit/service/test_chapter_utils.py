"""Tests for src/service/chapter/utils.py — pure path-array manipulation.

Strategy: for each function, the happy path is the assumption that
(1) the story exists, (2) it has a sane path_array, (3) the operation is
within bounds, and (4) idempotency holds. We test what happens when each
of those assumptions is violated.
"""
import pytest

from src.data.models import Chapter, Story
from src.service.chapter.utils import (
    append_chapter_to_path_end,
    handle_chapter_creation,
    handle_chapter_deletion,
    handle_chapter_reordering,
    remove_chapter_from_path,
    reorder_chapter_path,
    sync_all_chapter_pointers,
    update_story_timestamp,
)
from tests.factories import make_chapter, make_story, make_user


# ─── append_chapter_to_path_end ──────────────────────────────────────────────
class TestAppendChapterToPathEnd:
    async def test_raises_when_story_missing(self):
        with pytest.raises(ValueError, match="not found"):
            await append_chapter_to_path_end("missing-id", "ch-id")

    async def test_initialises_none_path_array_to_list_then_appends(self):
        user = await make_user()
        story = await Story.create(user_id=user.id, title="S", path_array=None)

        await append_chapter_to_path_end(story.id, "ch-1")

        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == ["ch-1"]

    async def test_is_idempotent_when_chapter_already_in_path(self):
        user = await make_user()
        story = await make_story(user, path_array=["ch-1"])

        await append_chapter_to_path_end(story.id, "ch-1")

        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == ["ch-1"]  # not duplicated

    async def test_appends_to_end_preserving_existing_order(self):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b"])

        await append_chapter_to_path_end(story.id, "c")

        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == ["a", "b", "c"]


# ─── remove_chapter_from_path ────────────────────────────────────────────────
class TestRemoveChapterFromPath:
    async def test_no_op_when_story_missing(self):
        # Assumption: caller does not need confirmation; missing == nothing to do
        await remove_chapter_from_path("missing", "ch")  # must not raise

    async def test_no_op_when_path_array_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        await remove_chapter_from_path(story.id, "ch-1")
        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == []

    async def test_no_op_when_chapter_not_in_path(self):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b"])
        await remove_chapter_from_path(story.id, "ghost")
        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == ["a", "b"]

    async def test_removes_only_the_target_chapter_preserving_order(self):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c"])

        await remove_chapter_from_path(story.id, "b")

        refreshed = await Story.get(id=story.id)
        assert refreshed.path_array == ["a", "c"]


# ─── reorder_chapter_path ────────────────────────────────────────────────────
class TestReorderChapterPath:
    async def test_no_op_when_story_missing(self):
        await reorder_chapter_path("missing", 0, 1)

    async def test_no_op_when_path_array_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        await reorder_chapter_path(story.id, 0, 0)
        assert (await Story.get(id=story.id)).path_array == []

    @pytest.mark.parametrize("from_pos,to_pos", [(-1, 0), (5, 0), (0, -1), (0, 5)])
    async def test_silently_returns_on_out_of_bounds_index(self, from_pos, to_pos):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c"])

        await reorder_chapter_path(story.id, from_pos, to_pos)

        # Path unchanged when bounds are violated
        assert (await Story.get(id=story.id)).path_array == ["a", "b", "c"]

    async def test_no_op_when_from_equals_to(self):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c"])
        await reorder_chapter_path(story.id, 1, 1)
        assert (await Story.get(id=story.id)).path_array == ["a", "b", "c"]

    async def test_moves_element_via_pop_then_insert(self):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c", "d"])

        await reorder_chapter_path(story.id, 0, 2)

        # Standard list semantics: pop(0) then insert(2, "a") -> [b,c,a,d]
        assert (await Story.get(id=story.id)).path_array == ["b", "c", "a", "d"]


# ─── sync_all_chapter_pointers ───────────────────────────────────────────────
class TestSyncAllChapterPointers:
    async def test_no_op_when_story_missing(self):
        await sync_all_chapter_pointers("missing")  # must not raise

    async def test_no_op_when_path_array_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        await sync_all_chapter_pointers(story.id)  # must not raise

    async def test_assumes_path_array_entries_reference_real_chapters(self):
        # Documents the implicit assumption: path_array must only hold ids of
        # chapters that exist. If it doesn't, the FK on prev/next_chapter_id
        # rejects the resulting bulk_update. Caller is responsible for keeping
        # path_array in sync with the chapters table.
        from tortoise.exceptions import IntegrityError

        user = await make_user()
        story = await make_story(user, path_array=[])
        ch = await make_chapter(story, user)
        story.path_array = [ch.id, "ghost-id"]
        await story.save(update_fields=["path_array"])

        with pytest.raises(IntegrityError):
            await sync_all_chapter_pointers(story.id)

    async def test_first_chapter_has_no_prev_and_last_has_no_next(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        a = await make_chapter(story, user, title="a")
        b = await make_chapter(story, user, title="b")
        c = await make_chapter(story, user, title="c")

        await sync_all_chapter_pointers(story.id)

        a, b, c = (await Chapter.get(id=a.id),
                   await Chapter.get(id=b.id),
                   await Chapter.get(id=c.id))
        assert a.prev_chapter_id is None and a.next_chapter_id == b.id
        assert b.prev_chapter_id == a.id and b.next_chapter_id == c.id
        assert c.prev_chapter_id == b.id and c.next_chapter_id is None


# ─── update_story_timestamp ──────────────────────────────────────────────────
class TestUpdateStoryTimestamp:
    async def test_filter_by_unknown_id_is_silent_noop(self):
        # Assumption tested: caller doesn't get an error if story id is bogus
        await update_story_timestamp("missing")  # tortoise update returns 0

    async def test_updates_only_updated_at_not_other_fields(self):
        user = await make_user()
        story = await make_story(user, title="original")
        original_ts = story.updated_at

        await update_story_timestamp(story.id)

        refreshed = await Story.get(id=story.id)
        assert refreshed.updated_at > original_ts
        assert refreshed.title == "original"


# ─── handle_chapter_creation / deletion / reordering ─────────────────────────
def _track(order: list[str], label: str):
    def _record(*_a, **_kw):
        order.append(label)
    return _record


class TestHandleChapterCreation:
    async def test_invokes_append_sync_and_timestamp_in_order(self, mocker):
        # Assumption: orchestration calls the three steps in order
        order: list[str] = []
        mocker.patch(
            "src.service.chapter.utils.append_chapter_to_path_end",
            new=mocker.AsyncMock(side_effect=_track(order, "append")),
        )
        mocker.patch(
            "src.service.chapter.utils.sync_all_chapter_pointers",
            new=mocker.AsyncMock(side_effect=_track(order, "sync")),
        )
        mocker.patch(
            "src.service.chapter.utils.update_story_timestamp",
            new=mocker.AsyncMock(side_effect=_track(order, "ts")),
        )

        await handle_chapter_creation("story-id", "ch-id")

        assert order == ["append", "sync", "ts"]


class TestHandleChapterDeletion:
    async def test_invokes_remove_sync_and_timestamp_in_order(self, mocker):
        order: list[str] = []
        mocker.patch(
            "src.service.chapter.utils.remove_chapter_from_path",
            new=mocker.AsyncMock(side_effect=_track(order, "remove")),
        )
        mocker.patch(
            "src.service.chapter.utils.sync_all_chapter_pointers",
            new=mocker.AsyncMock(side_effect=_track(order, "sync")),
        )
        mocker.patch(
            "src.service.chapter.utils.update_story_timestamp",
            new=mocker.AsyncMock(side_effect=_track(order, "ts")),
        )

        await handle_chapter_deletion("story-id", "ch-id")

        assert order == ["remove", "sync", "ts"]


class TestHandleChapterReordering:
    async def test_invokes_reorder_sync_and_timestamp_in_order(self, mocker):
        order: list[str] = []
        mocker.patch(
            "src.service.chapter.utils.reorder_chapter_path",
            new=mocker.AsyncMock(side_effect=_track(order, "reorder")),
        )
        mocker.patch(
            "src.service.chapter.utils.sync_all_chapter_pointers",
            new=mocker.AsyncMock(side_effect=_track(order, "sync")),
        )
        mocker.patch(
            "src.service.chapter.utils.update_story_timestamp",
            new=mocker.AsyncMock(side_effect=_track(order, "ts")),
        )

        await handle_chapter_reordering("story-id", 0, 1)

        assert order == ["reorder", "sync", "ts"]
