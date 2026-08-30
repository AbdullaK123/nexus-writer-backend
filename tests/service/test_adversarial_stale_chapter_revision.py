import pytest

from src.data.schemas.auth import UserResponse
from src.data.schemas.chapter import CreateChapterRequest, UpdateChapterRequest
from src.service.chapter.service import ChapterService
from src.service.exceptions import ConflictError
from tests.service.mocks import FakeChapterRepository, FakeStoryRepository


async def test_stale_chapter_revision_is_rejected_without_overwriting_newer_content(
    chapter_service: ChapterService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Revision conflict target",
    )
    chapter = await chapter_service.create_chapter(
        story.id,
        test_user.id,
        CreateChapterRequest(title="Shared chapter"),
    )

    stale_revision = chapter.revision
    assert stale_revision is not None

    first = await chapter_service.update_chapter(
        chapter.id,
        test_user.id,
        UpdateChapterRequest(
            content="TAB A COMMITTED",
            expected_revision=stale_revision,
        ),
    )
    assert first.content == "TAB A COMMITTED"
    assert first.revision is not None
    assert first.revision != stale_revision

    with pytest.raises(
        ConflictError,
        match="changed since you opened it",
    ):
        await chapter_service.update_chapter(
            chapter.id,
            test_user.id,
            UpdateChapterRequest(
                content="TAB B STALE OVERWRITE",
                expected_revision=stale_revision,
            ),
        )

    persisted = await fake_chapter_repo.get(chapter.id, test_user.id)
    assert persisted is not None
    assert persisted.content == "TAB A COMMITTED", (
        "a stale revision must fail closed; returning 409 is meaningless if the stale write "
        "already overwrote the newer canonical chapter"
    )
