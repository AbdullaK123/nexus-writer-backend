import pytest

from src.data.schemas.auth import UserResponse
from src.service.exceptions import NotFoundError
from src.service.story.service import StoryService
from tests.service.mocks import FakeAIProvider, FakeStoryRepository


async def test_foreign_story_search_is_rejected_before_paid_ai_work(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_provider: FakeAIProvider,
):
    foreign_story = await fake_story_repo.create(
        user_id="attacker-does-not-own-this-story",
        title="Foreign story",
    )

    with pytest.raises(NotFoundError):
        await story_service.search_story_scenes(
            user_id=test_user.id,
            story_id=foreign_story.id,
            query_text="Tell me what happens here",
        )

    assert fake_provider.call_count == 0, (
        "authorization must happen before embeddings or any other paid AI work; "
        "a valid foreign story id must be indistinguishable from a missing id"
    )


async def test_foreign_story_context_is_not_reported_as_merely_empty(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
):
    foreign_story = await fake_story_repo.create(
        user_id="attacker-does-not-own-this-story",
        title="Foreign story",
    )

    with pytest.raises(NotFoundError):
        await story_service.get_story_context(
            user_id=test_user.id,
            story_id=foreign_story.id,
        )
