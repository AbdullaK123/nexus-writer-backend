from src.data.schemas.auth import UserResponse
from src.data.schemas.extraction import INSUFFICIENT_CONTEXT
from src.service.story.service import StoryService
from tests.service.mocks import FakeAIProvider, FakeRedis, FakeStoryRepository


async def test_corrupt_pulse_cache_is_treated_as_miss_not_permanent_api_failure(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_redis: FakeRedis,
    fake_provider: FakeAIProvider,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Cache victim",
    )
    cache_key = f"pulse:{story.id}:{test_user.id}"
    fake_redis.poison(cache_key, "this is not valid cached JSON")

    result = await story_service.get_pulse(test_user.id, story.id)

    assert result == INSUFFICIENT_CONTEXT
    assert fake_provider.call_count == 0
    assert fake_redis.peek(cache_key) is None, (
        "one malformed Redis value must not brick the endpoint until TTL expiry; corrupt "
        "derived cache data should be evicted and recomputed from canonical state"
    )
