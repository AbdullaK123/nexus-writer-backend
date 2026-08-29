from src.data.schemas.auth import UserResponse
from src.data.schemas.enums import StoryStatus
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.service.story.service import StoryService
from tests.service.mocks import FakeStoryRepository


async def test_status_filter_never_leaks_stories_from_other_statuses(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
) -> None:
    await story_service.create_story(test_user.id, CreateStoryRequest(title="Ongoing"))
    await story_service.create_story(test_user.id, CreateStoryRequest(title="Complete"))

    complete = next(story for story in fake_story_repo._stories.values() if story.title == "Complete")
    await story_service.update_story(
        test_user.id,
        complete.id,
        UpdateStoryRequest(status=StoryStatus.COMPLETE),
    )

    result = await story_service.get_all_stories(test_user.id, status=StoryStatus.COMPLETE)

    assert [story.title for story in result.stories] == ["Complete"], (
        "a status-filtered endpoint must not return cards for stories outside the filter, "
        "even if their chapter query was filtered correctly"
    )
