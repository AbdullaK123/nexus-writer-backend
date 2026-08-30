import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.chapter import CreateChapterRequest, UpdateChapterRequest
from src.service.chapter.service import ChapterService
from src.service.exceptions import ServiceError
from tests.service.mocks import FakeChapterRepository, FakeQueue, FakeStoryRepository


async def test_failed_publish_enqueue_cannot_leave_chapter_published(
    chapter_service: ChapterService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_queue: FakeQueue,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Publish target",
    )
    chapter = await chapter_service.create_chapter(
        story.id,
        test_user.id,
        CreateChapterRequest(title="Chapter"),
    )

    long_content = "word " * 1100
    chapter = await chapter_service.update_chapter(
        chapter.id,
        test_user.id,
        UpdateChapterRequest(content=long_content),
    )
    assert chapter.published is False

    fake_queue.error = RuntimeError("queue unavailable after chapter commit")

    with pytest.raises(ServiceError):
        await chapter_service.update_chapter(
            chapter.id,
            test_user.id,
            UpdateChapterRequest(published=True),
        )

    persisted = await fake_chapter_repo.get(chapter.id, test_user.id)
    assert persisted is not None
    assert persisted.published is False, (
        "if publishing reports failure, the chapter must not already be published while its "
        "required extraction job failed to enqueue; committed state and API outcome must agree"
    )
