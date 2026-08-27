import pytest

from src.data.schemas.analytics import (
    Act,
    ActSegmentationExtraction,
    AnalyticsSuggestionExtraction,
    ContradictionExtraction,
    Entity,
    EntityLedgerExtraction,
    PlotThread,
    PlotThreadsExtraction,
)
from src.data.schemas.story import StoryRow
from tests.service.mocks import FakeAIProvider, FakeAnalyticsRepository, FakeStoryRepository


@pytest.fixture
def populated_analytics_repo(
    fake_analytics_repo: FakeAnalyticsRepository,
) -> FakeAnalyticsRepository:
    fake_analytics_repo.cast_statistics = [("Aria", 3, 1200)]
    fake_analytics_repo.co_occurrence_statistics = [("Aria", "Beren", 2, 800)]
    fake_analytics_repo.character_statistics = [
        ("chapter-1", 1, "Aria", 3, 1200),
    ]
    fake_analytics_repo.scene_length_distribution = [("0-499", 2), ("500-999", 1)]
    fake_analytics_repo.tension_and_pacing_curves = [
        ("chapter-1", 1, 3.5, 2.0, 3, 1200),
    ]
    fake_analytics_repo.recent_chapters_rythm = [
        ("chapter-1", 1, 3.5, 2.0, 3, 1200),
    ]
    fake_analytics_repo.questions_raised = [
        ("chapter-1", 1, "Who opened the eastern gate?"),
    ]
    return fake_analytics_repo


@pytest.fixture
def analytics_suggestion() -> AnalyticsSuggestionExtraction:
    return AnalyticsSuggestionExtraction(
        headline="The council thread is carrying the story",
        analysis="The supplied evidence shows the council thread receiving sustained attention.",
        status="healthy",
    )


@pytest.fixture
def plot_threads_extraction() -> PlotThreadsExtraction:
    return PlotThreadsExtraction(
        threads=[
            PlotThread(
                name="The Council Mystery",
                chapter_started=1,
                chapter_ended=None,
                chapter_last_touched=1,
                status="open",
            )
        ]
    )


@pytest.fixture
def act_segmentation_extraction() -> ActSegmentationExtraction:
    return ActSegmentationExtraction(
        acts=[
            Act(
                number=1,
                chapter_started=1,
                chapter_ended=None,
                current_chapter=1,
            )
        ]
    )


@pytest.fixture
def contradiction_extraction() -> ContradictionExtraction:
    return ContradictionExtraction(contradictions=[])


@pytest.fixture
def entity_ledger_extraction() -> EntityLedgerExtraction:
    return EntityLedgerExtraction(
        entities=[
            Entity(
                type="place",
                name="Eastern Gate",
                chapter_first_appeared=1,
                chapter_last_touched=1,
            )
        ]
    )


@pytest.fixture
def configured_analytics_provider(
    fake_provider: FakeAIProvider,
    analytics_suggestion: AnalyticsSuggestionExtraction,
    plot_threads_extraction: PlotThreadsExtraction,
    act_segmentation_extraction: ActSegmentationExtraction,
    contradiction_extraction: ContradictionExtraction,
    entity_ledger_extraction: EntityLedgerExtraction,
) -> FakeAIProvider:
    fake_provider.extract_responses = {
        AnalyticsSuggestionExtraction: analytics_suggestion,
        PlotThreadsExtraction: plot_threads_extraction,
        ActSegmentationExtraction: act_segmentation_extraction,
        ContradictionExtraction: contradiction_extraction,
        EntityLedgerExtraction: entity_ledger_extraction,
    }
    return fake_provider


@pytest.fixture
async def foreign_story(fake_story_repo: FakeStoryRepository) -> StoryRow:
    return await fake_story_repo.create(user_id="foreign-user", title="Foreign Story")
