import pytest
from src.data.schemas.auth import UserRow
from src.data.schemas.chapter import ChapterRow
from src.service.exceptions import NotFoundError
from src.service.extraction.service import ExtractionService
from lorem_text import lorem

from tests.service.mocks import FakeAIProvider, FakeChapterRepository, FakeSceneRepository


@pytest.mark.parametrize("content", [None, lorem.words(1000)])
async def test_raises_not_found_error(
    content: str,
    test_user: UserRow,
    extraction_service: ExtractionService
):
    with pytest.raises(NotFoundError):
        await extraction_service.extract_scenes(
            chapter_id="I don't exist",
            user_id=test_user.id,
            content=content
        )


async def test_chapter_not_long_enough(
    chapter_with_not_enough_content: ChapterRow,
    extraction_service: ExtractionService,
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository
):
    
    result = await extraction_service.extract_scenes(
        chapter_id=chapter_with_not_enough_content.id,
        user_id=chapter_with_not_enough_content.user_id
    )

    assert fake_provider.call_count == 0

    scenes = await fake_scene_repo.list_by_chapter(chapter_id=chapter_with_not_enough_content.id)

    assert scenes == []

    assert chapter_with_not_enough_content.scenes_extracted_at is not None