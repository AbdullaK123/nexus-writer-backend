from src.data.schemas.auth import UserResponse
from src.data.schemas.chapter import CreateChapterRequest
from src.service.chapter.service import ChapterService
from tests.service.mocks import FakeChapterRepository, FakeStoryRepository


async def test_chapter_read_honors_requested_content_representation(
    chapter_service: ChapterService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Representation Test",
    )
    created = await chapter_service.create_chapter(
        story.id,
        test_user.id,
        CreateChapterRequest(title="Chapter One"),
    )
    html = "<p>First paragraph</p><p>Second paragraph</p>"
    await fake_chapter_repo.update(
        chapter_id=created.id,
        user_id=test_user.id,
        fields={"content": html, "word_count": 4},
    )

    html_response = await chapter_service.get_chapter_with_navigation(
        created.id,
        test_user.id,
        as_html=True,
    )
    preview_response = await chapter_service.get_chapter_with_navigation(
        created.id,
        test_user.id,
        as_html=False,
    )

    assert html_response.content == html
    assert "<p>" not in preview_response.content, (
        "as_html=False must return the transformed preview rather than silently ignoring the representation requested by the caller"
    )
    assert "First paragraph" in preview_response.content
    assert "Second paragraph" in preview_response.content
    assert preview_response.content != html_response.content
