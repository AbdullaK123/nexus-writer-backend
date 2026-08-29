from src.data.schemas.auth import UserResponse
from src.data.schemas.chat import CreateThreadRequest
from src.data.schemas.story import StoryRow
from src.service.chat.service import ChatService
from src.shared.text_types import TITLE_MAX
from tests.service.mocks import FakeAIProvider, FakeChatRepository


async def test_generated_thread_title_cannot_persist_nul(
    chat_service: ChatService,
    test_user: UserResponse,
    test_story: StoryRow,
    fake_provider: FakeAIProvider,
    fake_chat_repo: FakeChatRepository,
) -> None:
    fake_provider.generate_response = "Normal looking\x00poisoned title"

    result = await chat_service.create_thread(
        test_user.id,
        CreateThreadRequest(
            story_id=test_story.id,
            first_message="Help me understand this chapter.",
        ),
    )

    stored = await fake_chat_repo.get_thread(result.thread_id, test_user.id)
    assert stored is not None
    assert "\x00" not in stored.title
    assert 1 <= len(stored.title) <= TITLE_MAX


async def test_generated_thread_title_is_bounded_before_persistence(
    chat_service: ChatService,
    test_user: UserResponse,
    test_story: StoryRow,
    fake_provider: FakeAIProvider,
    fake_chat_repo: FakeChatRepository,
) -> None:
    fake_provider.generate_response = "x" * (TITLE_MAX * 20)

    result = await chat_service.create_thread(
        test_user.id,
        CreateThreadRequest(
            story_id=test_story.id,
            first_message="Help me understand this chapter.",
        ),
    )

    stored = await fake_chat_repo.get_thread(result.thread_id, test_user.id)
    assert stored is not None
    assert 1 <= len(stored.title) <= TITLE_MAX


async def test_generated_thread_title_is_single_line_metadata(
    chat_service: ChatService,
    test_user: UserResponse,
    test_story: StoryRow,
    fake_provider: FakeAIProvider,
    fake_chat_repo: FakeChatRepository,
) -> None:
    fake_provider.generate_response = "  First line\n\tSecond line  "

    result = await chat_service.create_thread(
        test_user.id,
        CreateThreadRequest(
            story_id=test_story.id,
            first_message="Help me understand this chapter.",
        ),
    )

    stored = await fake_chat_repo.get_thread(result.thread_id, test_user.id)
    assert stored is not None
    assert stored.title == "First line Second line"
