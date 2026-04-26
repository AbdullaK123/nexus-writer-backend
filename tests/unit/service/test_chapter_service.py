"""Tests for src/service/chapter/service.py."""
import pytest

from src.data.models import Chapter, Story
from src.data.schemas.chapter import (
    CreateChapterRequest, ReorderChapterRequest, UpdateChapterRequest,
)
from src.service.chapter import service as chapter_service
from src.service.exceptions import (
    InternalError, NotFoundError, ValidationError,
)
from tests.factories import make_chapter, make_story, make_user


# ─── get_chapter_with_navigation ─────────────────────────────────────────────
class TestGetChapterWithNavigation:
    async def test_raises_not_found_when_chapter_doesnt_belong_to_user(self):
        # Assumption: filter scoped by both id AND user_id
        owner = await make_user(email="o@x.com")
        intruder = await make_user(email="i@x.com")
        story = await make_story(owner)
        ch = await make_chapter(story, owner)

        with pytest.raises(NotFoundError):
            await chapter_service.get_chapter_with_navigation(ch.id, intruder.id)

    async def test_raises_not_found_when_chapter_missing(self):
        user = await make_user()
        with pytest.raises(NotFoundError):
            await chapter_service.get_chapter_with_navigation("ghost", user.id)

    async def test_returns_full_html_when_as_html_true(self):
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(story, user, content="<p>full content</p>")

        resp = await chapter_service.get_chapter_with_navigation(
            ch.id, user.id, as_html=True)

        assert "full content" in resp.content

    async def test_returns_preview_when_as_html_false(self, mocker):
        # Assumption: as_html=False routes content through get_preview_content
        spy = mocker.patch(
            "src.service.chapter.service.get_preview_content",
            return_value="PREVIEW",
        )
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(story, user, content="<p>x</p>")

        resp = await chapter_service.get_chapter_with_navigation(
            ch.id, user.id, as_html=False)

        spy.assert_called_once()
        assert resp.content == "PREVIEW"


# ─── create ──────────────────────────────────────────────────────────────────
class TestCreate:
    async def test_raises_not_found_when_story_missing(self, mocker):
        # Assumption: story must exist before chapter is created
        spy = mocker.spy(Chapter, "create")
        user = await make_user()
        with pytest.raises(NotFoundError):
            await chapter_service.create(
                "ghost-story", user.id, CreateChapterRequest(title="X"))
        spy.assert_not_called()

    async def test_word_count_is_zero_when_content_is_empty(self, mocker):
        # Assumption: empty content -> word_count=0 without calling get_word_count
        spy = mocker.patch("src.service.chapter.service.get_word_count")
        user = await make_user()
        story = await make_story(user)

        await chapter_service.create(
            story.id, user.id, CreateChapterRequest(title="T", content=""))

        spy.assert_not_called()
        ch = await Chapter.get(story_id=story.id, title="T")
        assert ch.word_count == 0

    async def test_word_count_uses_get_word_count_for_non_empty_content(self, mocker):
        spy = mocker.patch(
            "src.service.chapter.service.get_word_count", return_value=42)
        user = await make_user()
        story = await make_story(user)

        await chapter_service.create(
            story.id, user.id,
            CreateChapterRequest(title="T", content="<p>hello</p>"))

        spy.assert_called_once_with("<p>hello</p>")
        ch = await Chapter.get(story_id=story.id, title="T")
        assert ch.word_count == 42

    async def test_invokes_handle_chapter_creation_after_persist(self, mocker):
        # Assumption: path_array bookkeeping happens after Chapter.create
        spy = mocker.patch(
            "src.service.chapter.service.handle_chapter_creation",
            new=mocker.AsyncMock(),
        )
        user = await make_user()
        story = await make_story(user)

        await chapter_service.create(
            story.id, user.id, CreateChapterRequest(title="T"))

        spy.assert_called_once()
        # First arg story_id, second arg = the new chapter id
        called_story_id, called_chapter_id = spy.call_args.args
        assert called_story_id == story.id
        assert await Chapter.filter(id=called_chapter_id).exists()

    async def test_wraps_unexpected_errors_in_internal_error(self, mocker):
        # Assumption: any non-ServiceError is reported as InternalError
        mocker.patch(
            "src.service.chapter.service.handle_chapter_creation",
            new=mocker.AsyncMock(side_effect=RuntimeError("boom")),
        )
        user = await make_user()
        story = await make_story(user)

        with pytest.raises(InternalError):
            await chapter_service.create(
                story.id, user.id, CreateChapterRequest(title="T"))

    async def test_passes_through_service_errors_unchanged(self, mocker):
        # Assumption: raised ServiceError subclasses are not re-wrapped
        mocker.patch(
            "src.service.chapter.service.handle_chapter_creation",
            new=mocker.AsyncMock(side_effect=ValidationError(message="bad")),
        )
        user = await make_user()
        story = await make_story(user)

        with pytest.raises(ValidationError):
            await chapter_service.create(
                story.id, user.id, CreateChapterRequest(title="T"))


# ─── update ──────────────────────────────────────────────────────────────────
class TestUpdate:
    async def test_raises_not_found_when_chapter_missing(self):
        user = await make_user()
        with pytest.raises(NotFoundError):
            await chapter_service.update(
                "ghost", user.id, UpdateChapterRequest(title="x"))

    async def test_raises_not_found_when_chapter_belongs_to_other_user(self):
        owner = await make_user(email="o@x.com")
        other = await make_user(email="x@x.com")
        story = await make_story(owner)
        ch = await make_chapter(story, owner)

        with pytest.raises(NotFoundError):
            await chapter_service.update(
                ch.id, other.id, UpdateChapterRequest(title="hax"))

    async def test_only_explicitly_set_fields_are_persisted(self):
        # Assumption: model_dump(exclude_unset=True)
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(
            story, user, title="orig", content="<p>orig</p>", word_count=99)

        await chapter_service.update(
            ch.id, user.id, UpdateChapterRequest())  # nothing set

        refreshed = await Chapter.get(id=ch.id)
        assert refreshed.title == "orig"
        assert refreshed.content == "<p>orig</p>"
        assert refreshed.word_count == 99

    async def test_word_count_recomputed_only_when_content_provided(self, mocker):
        # Assumption: word_count auto-updates iff content is in update payload
        spy = mocker.patch(
            "src.service.chapter.service.get_word_count", return_value=7)
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(story, user, word_count=99)

        # title-only update must not touch word_count
        await chapter_service.update(
            ch.id, user.id, UpdateChapterRequest(title="t"))
        spy.assert_not_called()
        assert (await Chapter.get(id=ch.id)).word_count == 99

        # content update recomputes
        await chapter_service.update(
            ch.id, user.id, UpdateChapterRequest(content="<p>new</p>"))
        spy.assert_called_once_with("<p>new</p>")
        assert (await Chapter.get(id=ch.id)).word_count == 7


# ─── delete ──────────────────────────────────────────────────────────────────
class TestDelete:
    async def test_raises_not_found_when_chapter_belongs_to_other_user(self):
        owner = await make_user(email="o@x.com")
        other = await make_user(email="x@x.com")
        story = await make_story(owner)
        ch = await make_chapter(story, owner)

        with pytest.raises(NotFoundError):
            await chapter_service.delete(ch.id, other.id)

        assert await Chapter.filter(id=ch.id).exists()

    async def test_invokes_handle_chapter_deletion_with_recorded_story_id(
        self, mocker,
    ):
        # Assumption: story_id is captured BEFORE the chapter is deleted
        # (after deletion, ch.story_id would still be in memory; this is the
        # invariant we encode)
        spy = mocker.patch(
            "src.service.chapter.service.handle_chapter_deletion",
            new=mocker.AsyncMock(),
        )
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(story, user)

        await chapter_service.delete(ch.id, user.id)

        spy.assert_called_once_with(story.id, ch.id)

    async def test_actually_deletes_the_row(self, mocker):
        mocker.patch(
            "src.service.chapter.service.handle_chapter_deletion",
            new=mocker.AsyncMock(),
        )
        user = await make_user()
        story = await make_story(user)
        ch = await make_chapter(story, user)

        await chapter_service.delete(ch.id, user.id)

        assert not await Chapter.filter(id=ch.id).exists()


# ─── get_story_chapters ──────────────────────────────────────────────────────
class TestGetStoryChapters:
    async def test_raises_not_found_when_story_belongs_to_other_user(self):
        owner = await make_user(email="o@x.com")
        other = await make_user(email="x@x.com")
        story = await make_story(owner)
        with pytest.raises(NotFoundError):
            await chapter_service.get_story_chapters(story.id, other.id)

    async def test_returns_empty_list_when_path_array_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        resp = await chapter_service.get_story_chapters(story.id, user.id)
        assert resp.chapters == []

    async def test_returns_empty_list_when_no_chapters_exist(self):
        # Assumption: even with stale path_array entries, no chapter rows
        # produces an empty list (not an error)
        user = await make_user()
        story = await make_story(user, path_array=["ghost-1"])
        resp = await chapter_service.get_story_chapters(story.id, user.id)
        assert resp.chapters == []

    async def test_skips_path_array_entries_with_no_matching_chapter(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        ch = await make_chapter(story, user, title="real")
        story.path_array = [ch.id, "ghost"]
        await story.save(update_fields=["path_array"])

        resp = await chapter_service.get_story_chapters(story.id, user.id)

        assert [c.id for c in resp.chapters] == [ch.id]

    async def test_orders_chapters_by_path_array_not_creation_time(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        a = await make_chapter(story, user, title="a", append_to_path=False)
        b = await make_chapter(story, user, title="b", append_to_path=False)
        story.path_array = [b.id, a.id]
        await story.save(update_fields=["path_array"])

        resp = await chapter_service.get_story_chapters(story.id, user.id)

        assert [c.id for c in resp.chapters] == [b.id, a.id]


# ─── reorder_chapters ────────────────────────────────────────────────────────
class TestReorderChapters:
    async def test_raises_not_found_when_story_belongs_to_other_user(self):
        owner = await make_user(email="o@x.com")
        other = await make_user(email="x@x.com")
        story = await make_story(owner, path_array=["a", "b"])
        with pytest.raises(NotFoundError):
            await chapter_service.reorder_chapters(
                story.id, other.id, ReorderChapterRequest(from_pos=0, to_pos=1))

    async def test_raises_validation_when_path_array_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        with pytest.raises(ValidationError):
            await chapter_service.reorder_chapters(
                story.id, user.id, ReorderChapterRequest(from_pos=0, to_pos=0))

    @pytest.mark.parametrize("from_pos", [-1, 5])
    async def test_raises_validation_when_from_pos_out_of_bounds(self, from_pos):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c"])
        with pytest.raises(ValidationError):
            await chapter_service.reorder_chapters(
                story.id, user.id,
                ReorderChapterRequest(from_pos=from_pos, to_pos=0))

    @pytest.mark.parametrize("to_pos", [-1, 5])
    async def test_raises_validation_when_to_pos_out_of_bounds(self, to_pos):
        user = await make_user()
        story = await make_story(user, path_array=["a", "b", "c"])
        with pytest.raises(ValidationError):
            await chapter_service.reorder_chapters(
                story.id, user.id,
                ReorderChapterRequest(from_pos=0, to_pos=to_pos))

    async def test_no_op_when_from_equals_to_does_not_invoke_handler(self, mocker):
        # Assumption: identical positions short-circuit before calling the job
        spy = mocker.patch(
            "src.service.chapter.service.handle_chapter_reordering",
            new=mocker.AsyncMock(),
        )
        user = await make_user()
        story = await make_story(user, path_array=["a", "b"])

        result = await chapter_service.reorder_chapters(
            story.id, user.id, ReorderChapterRequest(from_pos=1, to_pos=1))

        spy.assert_not_called()
        assert "No reordering" in result["message"]

    async def test_wraps_handler_failure_in_internal_error(self, mocker):
        # Assumption: any error from path-job is surfaced as InternalError
        mocker.patch(
            "src.service.chapter.service.handle_chapter_reordering",
            new=mocker.AsyncMock(side_effect=RuntimeError("boom")),
        )
        user = await make_user()
        story = await make_story(user, path_array=["a", "b"])

        with pytest.raises(InternalError):
            await chapter_service.reorder_chapters(
                story.id, user.id,
                ReorderChapterRequest(from_pos=0, to_pos=1))
