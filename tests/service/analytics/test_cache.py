from datetime import timedelta

import pytest

from src.data.schemas.analytics import AnalyticsSuggestionExtraction
from src.data.schemas.auth import UserResponse
from src.data.schemas.story import StoryRow
from src.service.analytics.service import AnalyticsService
from tests.service.mocks import FakeAIProvider, FakeAnalyticsRepository, FakeRedis


async def test_suggestion_cache_miss_invokes_ai_and_writes_scoped_cache(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
    fake_redis: FakeRedis,
) -> None:
    response = await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )

    key = f"suggestion:character:context-v2:{test_story.id}:{test_user.id}"
    assert response.story_id == test_story.id
    assert configured_analytics_provider.call_count == 1
    assert fake_redis.peek(key) is not None
    assert fake_redis.set_calls[-1][0] == key
    assert fake_redis.set_calls[-1][2] == timedelta(hours=1)


async def test_suggestion_cache_hit_skips_ai(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    first = await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )
    second = await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )

    assert second == first
    assert configured_analytics_provider.call_count == 1


async def test_ignore_cache_forces_fresh_suggestion(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )
    await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
        ignore_cache=True,
    )

    assert configured_analytics_provider.call_count == 2


async def test_suggestion_cache_does_not_leak_between_stories(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    other_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    first = await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )

    configured_analytics_provider.extract_responses[AnalyticsSuggestionExtraction] = (
        AnalyticsSuggestionExtraction(
            headline="Different story",
            analysis="This suggestion belongs only to the second story.",
            status="worth-watching",
        )
    )

    second = await analytics_service.get_analytics_suggestion(
        other_story.id,
        test_user.id,
        "character",
    )

    assert first.suggestion.headline != second.suggestion.headline
    assert configured_analytics_provider.call_count == 2


async def test_suggestion_cache_does_not_leak_between_users(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    foreign_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    first = await analytics_service.get_analytics_suggestion(
        test_story.id,
        test_user.id,
        "character",
    )

    configured_analytics_provider.extract_responses[AnalyticsSuggestionExtraction] = (
        AnalyticsSuggestionExtraction(
            headline="Foreign user suggestion",
            analysis="This suggestion belongs only to the foreign user's story.",
            status="healthy",
        )
    )

    second = await analytics_service.get_analytics_suggestion(
        foreign_story.id,
        foreign_story.user_id,
        "character",
    )

    assert first.suggestion.headline != second.suggestion.headline
    assert configured_analytics_provider.call_count == 2


async def test_failed_ai_suggestion_does_not_poison_cache(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    configured_analytics_provider: FakeAIProvider,
    fake_redis: FakeRedis,
) -> None:
    configured_analytics_provider.error = RuntimeError("provider failed")
    key = f"suggestion:character:context-v2:{test_story.id}:{test_user.id}"

    with pytest.raises(RuntimeError, match="provider failed"):
        await analytics_service.get_analytics_suggestion(
            test_story.id,
            test_user.id,
            "character",
        )

    assert fake_redis.peek(key) is None
