import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.story import StoryRow
from src.service.analytics.service import AnalyticsService
from src.service.exceptions import NotFoundError
from tests.service.mocks import FakeAIProvider, FakeAnalyticsRepository


async def test_missing_story_is_rejected(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
) -> None:
    with pytest.raises(NotFoundError, match="Story not found"):
        await analytics_service.get_cast_statistics("missing-story", test_user.id)


async def test_another_users_story_is_inaccessible(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    foreign_story: StoryRow,
) -> None:
    with pytest.raises(NotFoundError, match="Story not found"):
        await analytics_service.get_cast_statistics(foreign_story.id, test_user.id)


async def test_metric_query_is_scoped_by_story_and_user(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
) -> None:
    response = await analytics_service.get_cast_statistics(test_story.id, test_user.id)

    assert response.story_id == test_story.id
    assert response.story_title == test_story.title
    assert response.statistics[0].character == "Aria"
    assert populated_analytics_repo.calls == [("cast", test_story.id, test_user.id)]


async def test_empty_story_metric_returns_safe_empty_result_without_ai(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    fake_provider: FakeAIProvider,
) -> None:
    response = await analytics_service.get_cast_statistics(test_story.id, test_user.id)

    assert response.story_id == test_story.id
    assert response.statistics == []
    assert fake_provider.call_count == 0
