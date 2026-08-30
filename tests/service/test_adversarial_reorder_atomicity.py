import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.chapter import CreateChapterRequest, ReorderChapterRequest
from src.service.chapter.service import ChapterService
from src.service.exceptions import InternalError
from tests.service.mocks import FakeChapterRepository, FakeQueue, FakeStoryRepository


async def test_failed_reorder_side_effect_does_not_rollback_canonical_path(
    chapter_service: ChapterService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_queue: FakeQueue,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Reorder target",
    )

    first = await chapter_service.create_chapter(
        story.id,
        test_user.id,
        CreateChapterRequest(title="First"),
    )
    second = await chapter_service.create_chapter(
        story.id,
        test_user.id,
        CreateChapterRequest(title="Second"),
    )

    # Reanalysis enqueue only happens for published affected chapters.
    await fake_chapter_repo.update(
        chapter_id=first.id,
        user_id=test_user.id,
        fields={"published": True},
    )
    await fake_chapter_repo.update(
        chapter_id=second.id,
        user_id=test_user.id,
        fields={"published": True},
    )

    original_path = list(await fake_story_repo.get_path_array(story.id) or [])
    assert len(original_path) == 2

    fake_queue.error = RuntimeError("queue unavailable after database commit")

    with pytest.raises(InternalError):
        await chapter_service.reorder_chapters(
            story.id,
            test_user.id,
            ReorderChapterRequest(from_pos=0, to_pos=1),
        )

    final_path = list(await fake_story_repo.get_path_array(story.id) or [])
    assert final_path == [original_path[1], original_path[0]], (
        "chapter order is canonical state and must not be rolled back merely because derived "
        "reanalysis work fails after the database commit"
    )
