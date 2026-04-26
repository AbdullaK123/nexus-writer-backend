"""Tests for src/service/story/service.py."""
import pytest

from src.data.models import Chapter, Story
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.service.exceptions import ConflictError, NotFoundError
from src.service.story import service as story_service
from tests.factories import make_chapter, make_story, make_user


# ─── create ──────────────────────────────────────────────────────────────────
class TestCreate:
    async def test_raises_conflict_when_user_already_has_story_with_same_title(self):
        # Assumption: title is unique per user (composite (user_id, title))
        user = await make_user()
        await make_story(user, title="Same")

        with pytest.raises(ConflictError):
            await story_service.create(user.id, CreateStoryRequest(title="Same"))

    async def test_does_not_create_row_on_conflict(self):
        user = await make_user()
        await make_story(user, title="Same")
        before = await Story.filter(user_id=user.id).count()

        with pytest.raises(ConflictError):
            await story_service.create(user.id, CreateStoryRequest(title="Same"))

        assert await Story.filter(user_id=user.id).count() == before

    async def test_two_users_can_share_a_title(self):
        # Assumption: uniqueness scoped to user_id, not global
        user_a = await make_user(email="a@x.com")
        user_b = await make_user(email="b@x.com")
        await story_service.create(user_a.id, CreateStoryRequest(title="Shared"))
        await story_service.create(user_b.id, CreateStoryRequest(title="Shared"))
        assert await Story.filter(title="Shared").count() == 2

    async def test_initializes_path_array_to_empty_list(self):
        user = await make_user()
        await story_service.create(user.id, CreateStoryRequest(title="New"))
        story = await Story.get(user_id=user.id, title="New")
        assert story.path_array == []


# ─── update ──────────────────────────────────────────────────────────────────
class TestUpdate:
    async def test_raises_not_found_when_story_doesnt_belong_to_user(self):
        # Assumption: filter scopes by both id and user_id
        owner = await make_user(email="o@x.com")
        intruder = await make_user(email="i@x.com")
        story = await make_story(owner, title="O")

        with pytest.raises(NotFoundError):
            await story_service.update(
                intruder.id, story.id, UpdateStoryRequest(title="hax"))

    async def test_only_explicitly_set_fields_are_updated(self):
        # Assumption: model_dump(exclude_unset=True) drives the update
        user = await make_user()
        story = await make_story(user, title="orig")

        await story_service.update(
            user.id, story.id, UpdateStoryRequest())  # all fields unset

        refreshed = await Story.get(id=story.id)
        assert refreshed.title == "orig"  # unchanged

    async def test_updates_supplied_field_only(self):
        user = await make_user()
        story = await make_story(user, title="orig")

        await story_service.update(
            user.id, story.id, UpdateStoryRequest(title="new"))

        assert (await Story.get(id=story.id)).title == "new"


# ─── delete ──────────────────────────────────────────────────────────────────
class TestDelete:
    async def test_raises_not_found_when_story_belongs_to_someone_else(self):
        owner = await make_user(email="o@x.com")
        intruder = await make_user(email="i@x.com")
        story = await make_story(owner)

        with pytest.raises(NotFoundError):
            await story_service.delete(intruder.id, story.id)

        assert await Story.filter(id=story.id).exists()

    async def test_removes_story_row(self):
        user = await make_user()
        story = await make_story(user)
        await story_service.delete(user.id, story.id)
        assert not await Story.filter(id=story.id).exists()

    async def test_cascades_to_chapters(self):
        # Assumption: on_delete=CASCADE on Chapter.story FK removes children
        user = await make_user()
        story = await make_story(user)
        await make_chapter(story, user)
        await story_service.delete(user.id, story.id)
        assert await Chapter.filter(story_id=story.id).count() == 0


# ─── get_ordered_chapters ────────────────────────────────────────────────────
class TestGetOrderedChapters:
    async def test_raises_not_found_when_story_missing(self):
        user = await make_user()
        with pytest.raises(NotFoundError):
            await story_service.get_ordered_chapters(user.id, "missing")

    async def test_falls_back_to_created_at_desc_when_path_array_empty(self):
        # Assumption: empty path_array → reverse-chronological by created_at
        user = await make_user()
        story = await make_story(user, path_array=[])
        c1 = await make_chapter(story, user, title="first", append_to_path=False)
        c2 = await make_chapter(story, user, title="second", append_to_path=False)

        result = await story_service.get_ordered_chapters(user.id, story.id)

        assert [c.id for c in result] == [c2.id, c1.id]

    async def test_skips_path_array_entries_with_no_matching_chapter(self):
        # Assumption: path_array may drift; missing ids are silently skipped
        user = await make_user()
        story = await make_story(user, path_array=[])
        c1 = await make_chapter(story, user, title="real")
        # Inject ghost id
        story.path_array = [c1.id, "ghost"]
        await story.save(update_fields=["path_array"])

        result = await story_service.get_ordered_chapters(user.id, story.id)

        assert [c.id for c in result] == [c1.id]

    async def test_orders_chapters_by_path_array(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        a = await make_chapter(story, user, title="a", append_to_path=False)
        b = await make_chapter(story, user, title="b", append_to_path=False)
        c = await make_chapter(story, user, title="c", append_to_path=False)
        story.path_array = [c.id, a.id, b.id]
        await story.save(update_fields=["path_array"])

        result = await story_service.get_ordered_chapters(user.id, story.id)

        assert [ch.id for ch in result] == [c.id, a.id, b.id]


# ─── get_story_details ───────────────────────────────────────────────────────
class TestGetStoryDetails:
    async def test_raises_not_found_when_story_missing(self):
        user = await make_user()
        with pytest.raises(NotFoundError):
            await story_service.get_story_details(user.id, "missing")

    async def test_returns_details_with_zero_chapters_when_empty(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        resp = await story_service.get_story_details(user.id, story.id)
        assert resp.total_chapters == 0
        assert resp.chapters == []
        assert resp.word_count == 0

    async def test_word_count_aggregates_chapter_word_counts(self):
        user = await make_user()
        story = await make_story(user, path_array=[])
        await make_chapter(story, user, title="a", word_count=100)
        await make_chapter(story, user, title="b", word_count=250)
        resp = await story_service.get_story_details(user.id, story.id)
        assert resp.word_count == 350
        assert resp.total_chapters == 2


# ─── get_all_stories ─────────────────────────────────────────────────────────
class TestGetAllStories:
    async def test_returns_empty_grid_when_user_has_no_stories(self):
        user = await make_user()
        resp = await story_service.get_all_stories(user.id)
        assert resp.stories == []

    async def test_does_not_leak_other_users_stories(self):
        # Assumption: filter is scoped to user_id
        owner = await make_user(email="o@x.com")
        other = await make_user(email="x@x.com")
        await make_story(owner, title="mine")
        await make_story(other, title="theirs")

        resp = await story_service.get_all_stories(owner.id)

        assert {s.title for s in resp.stories} == {"mine"}

    async def test_orders_by_created_at_desc(self):
        # Assumption: order_by("-created_at")
        user = await make_user()
        await make_story(user, title="first")
        await make_story(user, title="second")
        await make_story(user, title="third")
        resp = await story_service.get_all_stories(user.id)
        assert [s.title for s in resp.stories] == ["third", "second", "first"]

    async def test_groups_chapters_by_story_when_aggregating_word_count(self):
        # Assumption: chapters keyed by story_id; counts must not bleed across
        user = await make_user()
        s1 = await make_story(user, title="s1")
        s2 = await make_story(user, title="s2")
        await make_chapter(s1, user, title="a", word_count=10)
        await make_chapter(s2, user, title="b", word_count=20)

        resp = await story_service.get_all_stories(user.id)
        by_title = {s.title: s for s in resp.stories}
        assert by_title["s1"].word_count == 10
        assert by_title["s2"].word_count == 20
