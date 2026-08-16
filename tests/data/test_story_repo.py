
import asyncpg
from src.data.repositories.story import StoryRepository
from tests.data.factories import make_user, make_story, make_chapter, make_scene

async def test_get_story_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    result_b = await repo.get(story_id=story.id, user_id=user_b.id)

    assert result_b is None


async def test_list_for_user_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    result_a = await repo.list_for_user(user_id=user_a.id)
    result_b = await repo.list_for_user(user_id=user_b.id)

    assert len(result_b) == 0 and len(result_a) > 0


async def test_exists_with_title_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    result_a = await repo.exists_with_title(user_id=user_a.id, title=story.title)
    result_b = await repo.exists_with_title(user_id=user_b.id, title=story.title)

    assert result_a != result_b


async def test_update_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    await repo.update(story_id=story.id, user_id=user_a.id, fields={"title": "Updated title"})
    await repo.update(story_id=story.id, user_id=user_b.id, fields={"title": "Updated title again"})

    refetched_story = await repo.get(story.id, user_id=user_a.id)

    assert refetched_story is not None and refetched_story.title == "Updated title"

async def test_delete_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    result = await repo.delete(story_id=story.id, user_id=user_b.id)

    assert result == False

async def test_get_stats_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = StoryRepository(clean_db)

    result_a = await repo.get_stats(story_id=story.id, user_id=user_a.id)
    result_b = await repo.get_stats(story_id=story.id, user_id=user_b.id)


    assert result_a != result_b
