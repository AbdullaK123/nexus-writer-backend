import asyncio

import pytest

from src.data.repositories.chat import ChatRepository
from src.data.schemas.auth import UserRow
from src.data.schemas.chat import ChatThreadRow
from src.data.schemas.story import StoryRow


REQUEST_MESSAGE = {"kind": "request", "parts": [{"content": "Hello"}]}
RESPONSE_MESSAGE = {"kind": "response", "parts": [{"content": "Hi"}]}


async def test_create_and_get_thread_are_scoped_to_owner(
    chat_repo: ChatRepository,
    repo_user: UserRow,
    repo_other_user: UserRow,
    repo_story: StoryRow,
) -> None:
    thread = await chat_repo.create_thread(repo_user.id, repo_story.id, "My Thread")

    owner_result = await chat_repo.get_thread(thread.id, repo_user.id)
    foreign_result = await chat_repo.get_thread(thread.id, repo_other_user.id)

    assert owner_result is not None
    assert owner_result.title == "My Thread"
    assert foreign_result is None


async def test_list_threads_for_story_is_scoped_and_newest_first(
    chat_repo: ChatRepository,
    repo_user: UserRow,
    repo_other_user: UserRow,
    repo_story: StoryRow,
    repo_other_story: StoryRow,
) -> None:
    first = await chat_repo.create_thread(repo_user.id, repo_story.id, "First")
    await asyncio.sleep(0.01)
    second = await chat_repo.create_thread(repo_user.id, repo_story.id, "Second")
    await chat_repo.create_thread(repo_user.id, repo_other_story.id, "Other Story")

    owner_threads = await chat_repo.list_threads_for_story(repo_user.id, repo_story.id)
    foreign_threads = await chat_repo.list_threads_for_story(
        repo_other_user.id,
        repo_story.id,
    )

    assert [thread.id for thread in owner_threads] == [second.id, first.id]
    assert all(thread.story_id == repo_story.id for thread in owner_threads)
    assert foreign_threads == []


async def test_update_title_only_changes_owning_users_thread(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
    repo_other_user: UserRow,
) -> None:
    foreign_update = await chat_repo.update_thread_title(
        repo_chat_thread.id,
        repo_other_user.id,
        "Foreign title",
    )
    owner_after_foreign_update = await chat_repo.get_thread(
        repo_chat_thread.id,
        repo_user.id,
    )

    owner_update = await chat_repo.update_thread_title(
        repo_chat_thread.id,
        repo_user.id,
        "Owner title",
    )

    assert foreign_update is None
    assert owner_after_foreign_update is not None
    assert owner_after_foreign_update.title == "Thread"
    assert owner_update is not None
    assert owner_update.title == "Owner title"


async def test_delete_thread_only_affects_owning_user(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
    repo_other_user: UserRow,
) -> None:
    await chat_repo.delete_thread(repo_chat_thread.id, repo_other_user.id)
    assert await chat_repo.get_thread(repo_chat_thread.id, repo_user.id) is not None

    await chat_repo.delete_thread(repo_chat_thread.id, repo_user.id)
    assert await chat_repo.get_thread(repo_chat_thread.id, repo_user.id) is None


async def test_append_messages_assigns_monotonic_sequence_and_lists_in_order(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
) -> None:
    first = await chat_repo.append_message(
        repo_chat_thread.id,
        repo_user.id,
        "request",
        REQUEST_MESSAGE,
    )
    second = await chat_repo.append_message(
        repo_chat_thread.id,
        repo_user.id,
        "response",
        RESPONSE_MESSAGE,
    )
    third = await chat_repo.append_message(
        repo_chat_thread.id,
        repo_user.id,
        "request",
        REQUEST_MESSAGE,
    )

    rows = await chat_repo.list_messages(repo_chat_thread.id, repo_user.id)

    assert [first.sequence, second.sequence, third.sequence] == [0, 1, 2]
    assert [row.sequence for row in rows] == [0, 1, 2]
    assert [row.kind for row in rows] == ["request", "response", "request"]
    assert rows[0].message == REQUEST_MESSAGE
    assert rows[1].message == RESPONSE_MESSAGE


async def test_list_messages_is_user_scoped(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
    repo_other_user: UserRow,
) -> None:
    await chat_repo.append_message(
        repo_chat_thread.id,
        repo_user.id,
        "request",
        REQUEST_MESSAGE,
    )

    assert await chat_repo.list_messages(repo_chat_thread.id, repo_other_user.id) == []


async def test_touch_thread_updates_timestamp(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
) -> None:
    await asyncio.sleep(0.01)
    await chat_repo.touch_thread(repo_chat_thread.id, repo_user.id)
    touched = await chat_repo.get_thread(repo_chat_thread.id, repo_user.id)

    assert touched is not None
    assert touched.updated_at > repo_chat_thread.updated_at


async def test_transaction_rollback_preserves_previous_thread_and_message_state(
    chat_repo: ChatRepository,
    repo_chat_thread: ChatThreadRow,
    repo_user: UserRow,
) -> None:
    with pytest.raises(RuntimeError, match="abort transaction"):
        async with chat_repo.pool.acquire() as conn:
            async with conn.transaction():
                await chat_repo.append_message(
                    repo_chat_thread.id,
                    repo_user.id,
                    "request",
                    REQUEST_MESSAGE,
                    executor=conn,
                )
                updated = await chat_repo.update_thread_title(
                    repo_chat_thread.id,
                    repo_user.id,
                    "Uncommitted title",
                    executor=conn,
                )
                assert updated is not None
                raise RuntimeError("abort transaction")

    thread = await chat_repo.get_thread(repo_chat_thread.id, repo_user.id)
    messages = await chat_repo.list_messages(repo_chat_thread.id, repo_user.id)

    assert thread is not None
    assert thread.title == repo_chat_thread.title
    assert messages == []
