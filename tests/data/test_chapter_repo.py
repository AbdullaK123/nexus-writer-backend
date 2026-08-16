
import asyncpg
from src.data.repositories.chapter import ChapterRepository
from tests.data.factories import make_user, make_story, make_chapter, make_scene

async def test_get_chapter_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = ChapterRepository(clean_db)

    result_b = await repo.get(chapter_id=chapter.id, user_id=user_b.id)

    assert result_b is None


async def test_get_with_story_title_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = ChapterRepository(clean_db)

    result = await repo.get_with_story_title(chapter_id=chapter.id, user_id=user_b.id)

    assert result is None


async def test_list_by_story_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = ChapterRepository(clean_db)

    result_a = await repo.list_by_story(user_id=user_a.id, story_id=story.id)
    result_b = await repo.list_by_story(user_id=user_b.id, story_id=story.id)

    assert len(result_a) > 0 and len(result_b) == 0


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

    repo = ChapterRepository(clean_db)

    await repo.update(chapter_id=chapter.id, user_id=user_a.id, fields={"title": "Updated title", "content": "<p>Updated content</p>", "published": True})
    await repo.update(chapter_id=chapter.id, user_id=user_b.id, fields={"title": "Updated title again", "content": "<p>Updated content again</p>", "published": False})

    refetched_chapter = await repo.get(chapter.id, user_id=user_a.id)

    assert refetched_chapter is not None and refetched_chapter.title == "Updated title" and refetched_chapter.content == "<p>Updated content</p>" and refetched_chapter.published

