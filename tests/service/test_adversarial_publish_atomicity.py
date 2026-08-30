from src.data.schemas.auth import UserResponse
from src.data.schemas.chapter import CreateChapterRequest, UpdateChapterRequest
from src.service.chapter.service import ChapterService
from tests.service.mocks import FakeChapterRepository, FakeQueue, FakeStoryRepository


async def test_failed_publish_enqueue_does_not_rollback_canonical_publish(
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

    fake_queue.error = ConnectionError("queue unavailable after chapter commit")

    updated = await chapter_service.update_chapter(
        chapter.id,
        test_user.id,
        UpdateChapterRequest(published=True),
    )

    assert updated.published is True

    persisted = await fake_chapter_repo.get(chapter.id, test_user.id)
    assert persisted is not None
    assert persisted.published is True, (
        "publishing is canonical state and must not be rolled back merely because derived "
        "extraction work exhausted its enqueue retries"
    )
