import asyncpg
from src.data.repositories.user import UserRepository
from tests.data.factories import make_user, make_story, make_chapter, make_scene

async def test_get_dashboard_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = UserRepository(clean_db)

    result_a = await repo.get_dashboard(user_id=user_a.id)
    result_b = await repo.get_dashboard(user_id=user_b.id)

    assert result_a != result_b


async def test_get_editor_links_isolation(
    clean_db: asyncpg.Pool
):

    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = UserRepository(clean_db)

    result_a = await repo.get_editor_link_params(user_id=user_a.id)
    result_b = await repo.get_editor_link_params(user_id=user_b.id)

    assert result_a != result_b


async def test_get_chat_links_isolation(
    clean_db: asyncpg.Pool
):

    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = UserRepository(clean_db)

    result_a = await repo.get_chat_link_params(user_id=user_a.id)
    result_b = await repo.get_chat_link_params(user_id=user_b.id)

    assert result_a != result_b


