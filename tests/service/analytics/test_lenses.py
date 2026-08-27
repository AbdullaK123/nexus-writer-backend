import pytest

from src.data.schemas.analytics import PlotThreadsExtraction
from src.data.schemas.auth import UserResponse
from src.data.schemas.story import StoryRow
from src.service.analytics.service import AnalyticsService
from src.service.exceptions import ServiceError
from tests.service.mocks import FakeAIProvider, FakeAnalyticsRepository


async def test_character_lens_uses_database_evidence_without_ai(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    fake_provider: FakeAIProvider,
) -> None:
    inputs = await analytics_service.get_prompt_inputs(
        test_story.id,
        test_user.id,
        "character",
    )

    assert "Aria" in inputs["cast_statistics"]
    assert "Beren" in inputs["co_occurrence_statistics"]
    assert "chapter-1" in inputs["character_statistics"]
    assert {call[0] for call in populated_analytics_repo.calls} == {
        "cast",
        "co_occurrence",
        "character",
    }
    assert fake_provider.call_count == 0


async def test_structure_lens_uses_database_evidence_without_ai(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    fake_provider: FakeAIProvider,
) -> None:
    inputs = await analytics_service.get_prompt_inputs(
        test_story.id,
        test_user.id,
        "structure",
    )

    assert "3.5" in inputs["tension_curve"]
    assert "2.0" in inputs["pacing_curve"]
    assert "0-499" in inputs["scene_length_distribution"]
    assert "chapter-1" in inputs["recent_chapter_rythm"]
    assert fake_provider.call_count == 0


async def test_questions_lens_uses_database_evidence_without_ai(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    populated_analytics_repo: FakeAnalyticsRepository,
    fake_provider: FakeAIProvider,
) -> None:
    inputs = await analytics_service.get_prompt_inputs(
        test_story.id,
        test_user.id,
        "questions",
    )

    assert "Who opened the eastern gate?" in inputs["questions_raised"]
    assert populated_analytics_repo.calls == [
        ("questions", test_story.id, test_user.id)
    ]
    assert fake_provider.call_count == 0


async def test_plot_lens_builds_inputs_from_plot_and_act_extractions(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    inputs = await analytics_service.get_prompt_inputs(
        test_story.id,
        test_user.id,
        "plot",
    )

    schemas = {call["schema"] for call in configured_analytics_provider.extract_calls}
    assert "The Council Mystery" in inputs["plot_threads"]
    assert "1" in inputs["act_segmentation"]
    assert len(schemas) == 2


async def test_world_lens_builds_inputs_from_entity_and_contradiction_extractions(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    inputs = await analytics_service.get_prompt_inputs(
        test_story.id,
        test_user.id,
        "world",
    )

    schemas = {call["schema"] for call in configured_analytics_provider.extract_calls}
    assert "Eastern Gate" in inputs["entity_ledger"]
    assert "headline" in inputs["contradictions"]
    assert len(schemas) == 2


async def test_malformed_plot_extraction_fails_safely(
    analytics_service: AnalyticsService,
    test_user: UserResponse,
    test_story: StoryRow,
    configured_analytics_provider: FakeAIProvider,
) -> None:
    configured_analytics_provider.extract_responses[PlotThreadsExtraction] = (
        PlotThreadsExtraction(threads=None)
    )

    with pytest.raises(ServiceError, match="get_prompt_inputs.failed"):
        await analytics_service.get_prompt_inputs(
            test_story.id,
            test_user.id,
            "plot",
        )
