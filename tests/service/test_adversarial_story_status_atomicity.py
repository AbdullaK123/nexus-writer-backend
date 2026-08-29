import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.enums import StoryStatus
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.service.exceptions import ServiceError
from src.service.story.service import StoryService
from tests.service.mocks import FakeRedis, FakeStoryRepository


async def test_failed_status_cache_invalidation_cannot_leave_status_committed(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_redis: FakeRedis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await story_service.create_story(
        test_user.id,
        CreateStoryRequest(title="Status target"),
    )
    story = next(iter(fake_story_repo._stories.values()))
    assert story.status == StoryStatus.ONGOING

    async def fail_delete(*keys: str) -> int:
        raise RuntimeError("redis unavailable after database update")

    monkeypatch.setattr(fake_redis, "delete", fail_delete)

    with pytest.raises(ServiceError):
        await story_service.update_story(
            test_user.id,
            story.id,
            UpdateStoryRequest(status=StoryStatus.COMPLETE),
        )

    persisted = await fake_story_repo.get(story.id, test_user.id)
    assert persisted is not None
    assert persisted.status == StoryStatus.ONGOING, (
        "a failed status mutation must not leave the new status committed while status-dependent "
        "analysis caches remain stale; API outcome, canonical state, and derived state must agree"
    )
