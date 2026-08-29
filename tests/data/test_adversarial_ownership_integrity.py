import asyncpg
import pytest

from src.data.repositories.chapter import ChapterRepository
from src.data.repositories.chat import ChatRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.story import StoryRow
from tests.data.factories import make_scene


async def test_database_rejects_chapter_owned_by_different_user_than_parent_story(
    clean_db: asyncpg.Pool,
    repo_story: StoryRow,
    repo_other_user: UserRow,
) -> None:
    repo = ChapterRepository(clean_db)

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        await repo.create(
            story_id=repo_story.id,
            user_id=repo_other_user.id,
            title="cross-tenant chapter",
            content="",
            word_count=0,
        )


async def test_database_rejects_chat_thread_owned_by_different_user_than_parent_story(
    clean_db: asyncpg.Pool,
    repo_story: StoryRow,
    repo_other_user: UserRow,
) -> None:
    repo = ChatRepository(clean_db)

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        await repo.create_thread(
            repo_other_user.id,
            repo_story.id,
            "cross-tenant thread",
        )


async def test_database_rejects_scene_whose_owner_disagrees_with_chapter_and_story(
    clean_db: asyncpg.Pool,
    repo_story: StoryRow,
    repo_user: UserRow,
    repo_other_user: UserRow,
) -> None:
    chapter_repo = ChapterRepository(clean_db)
    chapter = await chapter_repo.create(
        story_id=repo_story.id,
        user_id=repo_user.id,
        title="owned chapter",
        content="",
        word_count=0,
    )

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        await make_scene(
            clean_db,
            chapter_id=chapter.id,
            story_id=repo_story.id,
            user_id=repo_other_user.id,
        )


async def test_database_rejects_scene_pointing_at_chapter_from_another_story(
    clean_db: asyncpg.Pool,
    repo_story: StoryRow,
    repo_other_story: StoryRow,
    repo_user: UserRow,
) -> None:
    chapter_repo = ChapterRepository(clean_db)
    chapter = await chapter_repo.create(
        story_id=repo_story.id,
        user_id=repo_user.id,
        title="story A chapter",
        content="",
        word_count=0,
    )

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        await make_scene(
            clean_db,
            chapter_id=chapter.id,
            story_id=repo_other_story.id,
            user_id=repo_user.id,
        )
