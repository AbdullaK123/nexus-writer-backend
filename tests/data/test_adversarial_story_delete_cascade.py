import asyncpg

from src.data.repositories.chat import ChatRepository
from src.data.repositories.story import StoryRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.story import StoryRow
from tests.data.factories import make_chapter, make_scene


async def test_deleting_populated_story_leaves_no_relational_zombies(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
    repo_story: StoryRow,
) -> None:
    chapter = await make_chapter(
        clean_db,
        user_id=repo_user.id,
        story_id=repo_story.id,
    )
    scene = await make_scene(
        clean_db,
        chapter_id=chapter.id,
        story_id=repo_story.id,
        user_id=repo_user.id,
    )

    chat_repo = ChatRepository(clean_db)
    thread = await chat_repo.create_thread(
        repo_user.id,
        repo_story.id,
        "Thread to be destroyed",
    )
    message = await chat_repo.append_message(
        thread.id,
        repo_user.id,
        "request",
        {"kind": "request", "parts": [{"content": "hello"}]},
    )

    story_repo = StoryRepository(clean_db)
    assert await story_repo.delete(
        story_id=repo_story.id,
        user_id=repo_user.id,
    ) is True

    async with clean_db.acquire() as conn:
        counts = {
            "story": await conn.fetchval(
                'SELECT COUNT(*) FROM story WHERE id=$1', repo_story.id
            ),
            "chapter": await conn.fetchval(
                'SELECT COUNT(*) FROM chapter WHERE id=$1 OR story_id=$2',
                chapter.id,
                repo_story.id,
            ),
            "scene": await conn.fetchval(
                'SELECT COUNT(*) FROM scene WHERE id=$1 OR story_id=$2 OR chapter_id=$3',
                scene["id"],
                repo_story.id,
                chapter.id,
            ),
            "thread": await conn.fetchval(
                'SELECT COUNT(*) FROM chat_thread WHERE id=$1 OR story_id=$2',
                thread.id,
                repo_story.id,
            ),
            "message": await conn.fetchval(
                'SELECT COUNT(*) FROM chat_message WHERE id=$1 OR thread_id=$2',
                message.id,
                thread.id,
            ),
        }

    assert counts == {
        "story": 0,
        "chapter": 0,
        "scene": 0,
        "thread": 0,
        "message": 0,
    }, (
        "story deletion is an aggregate destruction boundary: no chapter, scene, thread, "
        "or message may survive as an orphan/zombie row"
    )
