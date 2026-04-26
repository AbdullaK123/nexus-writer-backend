"""Sanity check: schema generates and basic inserts work under SQLite."""
from src.data.models import User, Story
from tests.factories import make_user, make_story


async def test_schema_generates_and_user_inserts():
    user = await make_user()
    assert (await User.all().count()) == 1
    assert user.id


async def test_array_field_shim_round_trips_path_array():
    user = await make_user()
    story = await make_story(user, title="S", path_array=["a", "b", "c"])
    refreshed = await Story.get(id=story.id)
    assert refreshed.path_array == ["a", "b", "c"]
