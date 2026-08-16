import asyncpg
from src.data.repositories.scene import SceneRepository
from src.shared.utils.html import html_to_plain_text
from tests.data.factories import make_user, make_story, make_chapter, make_scene

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

    repo = SceneRepository(clean_db)

    result_b = await repo.list_by_story(story_id=story.id, user_id=user_b.id)

    assert len(result_b) == 0


async def test_search_scenes_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)

    search_term = html_to_plain_text(chapter.content or "")[10:20]

    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = SceneRepository(clean_db)

    result = await repo.search_scenes(
        user_id=user_b.id, 
        story_id=story.id, 
        query_text=search_term, 
        k=2, 
        candidate_pool=5, 
        query_embedding=[0, 0, 0, 0]
    )

    assert len(result) == 0


async def test_list_story_tags_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = SceneRepository(clean_db)

    result_b = await repo.list_story_tags(user_id=user_b.id, story_id=story.id)

    assert len(result_b) == 0


async def test_list_story_entities_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = SceneRepository(clean_db)

    result_b = await repo.list_story_entities(user_id=user_b.id, story_id=story.id)
    
    assert len(result_b) == 0


async def test_list_povs_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)

    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = SceneRepository(clean_db)

    result_b = await repo.list_povs(user_id=user_b.id, story_id=story.id)
        
    assert len(result_b) == 0

