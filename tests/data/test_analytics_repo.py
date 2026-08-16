import asyncpg
from src.data.repositories.analytics import AnalyticsRepository
from src.shared.utils.html import html_to_plain_text
from tests.data.factories import make_user, make_story, make_chapter, make_scene


async def test_get_cast_statistics_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_cast_statistics(story.id, user_id=user_b.id)

    assert len(result) == 0

async def test_get_character_co_occurence_statistics_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_character_co_occurence_statistics(story.id, user_id=user_b.id)

    assert len(result) == 0

async def test_get_character_statistics_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_character_statistics(story.id, user_id=user_b.id)

    assert len(result) == 0


async def test_get_scene_length_distribution_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_scene_length_distribution(story.id, user_id=user_b.id)

    assert len(result) == 0

async def test_get_tension_and_pacing_curves_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_tension_and_pacing_curves(story.id, user_id=user_b.id)

    assert len(result) == 0

async def test_get_recent_chapters_rythm_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_recent_chapters_rythm(story.id, user_id=user_b.id)

    assert len(result) == 0


async def test_get_entity_statistics_isolation(
    clean_db: asyncpg.Pool
):
    user_a = await make_user(clean_db)
    user_b = await make_user(clean_db)
    
    story = await make_story(clean_db, user_id=user_a.id)
    chapter = await make_chapter(clean_db, user_id=user_a.id, story_id=story.id)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=0)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=1)
    await make_scene(clean_db, chapter_id=chapter.id, story_id=story.id, user_id=user_a.id, position=2)

    repo = AnalyticsRepository(clean_db)

    result = await repo.get_entity_statistics(story.id, user_id=user_b.id)

    assert len(result) == 0