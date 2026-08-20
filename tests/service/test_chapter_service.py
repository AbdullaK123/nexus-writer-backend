import pytest
from src.data.schemas.auth import RegistrationData, UserResponse
from src.data.schemas.chapter import ChapterRow, CreateChapterRequest, UpdateChapterRequest
from src.data.schemas.story import StoryRow
from src.service.auth.service import AuthService
from src.service.chapter.service import ChapterService
from src.service.exceptions import InternalError, NotFoundError
from src.shared.utils.html import html_to_plain_text
from tests.service.mocks import FakeChapterRepository, FakeQueue, FakeRedis, FakeStoryRepository
from lorem_text import lorem

async def test_chapter_with_navigation_not_found_path(
    test_user: UserResponse,
    chapter_service: ChapterService
):
    with pytest.raises(NotFoundError):
        await chapter_service.get_chapter_with_navigation(
            chapter_id="I don't exist",
            user_id=test_user.id,
        )


class TestGetStoryChapters:

    async def test_not_found_path(
        self,
        test_user: UserResponse,
        chapter_service: ChapterService
    ):
        with pytest.raises(NotFoundError):
            await chapter_service.get_story_chapters(
                story_id="I don't exist",
                user_id=test_user.id
            )

    async def test_empty_path_array(
        self,
        test_user: UserResponse,
        test_story: StoryRow,
        chapter_service: ChapterService
    ):
        result = await chapter_service.get_story_chapters(
            story_id=test_story.id,
            user_id=test_user.id
        )
        assert result.chapters == []


class TestCreateChapter:

    async def test_not_found_path(
        self,
        test_user: UserResponse,
        chapter_service: ChapterService
    ):
        with pytest.raises(NotFoundError):
            await chapter_service.create_chapter(
                story_id="I don't exist",
                user_id=test_user.id,
                data=CreateChapterRequest(
                    title="test"
                )
            )

    async def test_mid_failure(
        self,
        test_user: UserResponse,
        test_story: StoryRow,
        fake_chapter_repo: FakeChapterRepository,
        chapter_service: ChapterService
    ):
        fake_chapter_repo.error = RuntimeError("KABOOM!")
        with pytest.raises(InternalError, match="Something went wrong while creating your chapter. Please try again."):
            await chapter_service.create_chapter(
                story_id=test_story.id,
                user_id=test_user.id,
                data=CreateChapterRequest(
                    title="test"
                )
            )


class TestUpdateChapter:

    async def test_not_found_path(
        self,
        test_user: UserResponse,
        chapter_service: ChapterService
    ):
        with pytest.raises(NotFoundError):
            await chapter_service.update_chapter(
                chapter_id="I don't exist",
                user_id=test_user.id,
                data=UpdateChapterRequest(
                    title="updated",
                    content="new content"
                )
            )

    async def test_deleted_between_get_and_update(
        self,
        test_user: UserResponse,
        test_chapter: ChapterRow,
        fake_chapter_repo: FakeChapterRepository,
        chapter_service: ChapterService
    ):
        fake_chapter_repo.force_return_none = True
        with pytest.raises(NotFoundError):
            await chapter_service.update_chapter(
                chapter_id=test_chapter.id,
                user_id=test_user.id,
                data=UpdateChapterRequest(
                    title="updated",
                    content="new content"
                )
            )

    async def test_published_chapter_with_enough_content_gets_enqueued(
        self,
        test_user: UserResponse,
        chapter_with_enough_content: ChapterRow,
        fake_redis: FakeRedis,
        chapter_service: ChapterService
    ):
        await chapter_service.update_chapter(
            chapter_id=chapter_with_enough_content.id,
            user_id=test_user.id,
            data=UpdateChapterRequest(
                published=True
            )
        )
        pending_key = f"chapter:extraction-pending:{chapter_with_enough_content.id}"
        key = await fake_redis.get(pending_key)
        assert key is not None

    async def test_published_chapter_with_not_enough_content_does_not_get_enqueued(
        self,
        test_user: UserResponse,
        chapter_with_not_enough_content: ChapterRow,
        fake_redis: FakeRedis,
        chapter_service: ChapterService
    ):
        await chapter_service.update_chapter(
            chapter_id=chapter_with_not_enough_content.id,
            user_id=test_user.id,
            data=UpdateChapterRequest(
                published=True
            )
        )
        pending_key = f"chapter:extraction-pending:{chapter_with_not_enough_content.id}"
        key = await fake_redis.get(pending_key)
        assert key is None

    async def test_cache_invalidation(
        self,
        test_user: UserResponse,
        chapter_with_enough_content: ChapterRow,
        fake_queue: FakeQueue,
        fake_redis: FakeRedis,
        chapter_service: ChapterService
    ):
        chapter = await chapter_service.update_chapter(
            chapter_id=chapter_with_enough_content.id,
            user_id=test_user.id,
            data=UpdateChapterRequest(
                published=True
            )
        )

        keys = [
            f"chapter:baseline:{chapter.id}",
            f"chapter:extraction-pending:{chapter.id}",
            f"chapter:editorial_plan:{test_user.id}:{chapter.id}",
            f"summary:{chapter.id}:{test_user.id}",
            f"chapter:comments:{chapter.id}",
            f"pulse:{chapter.story_id}:{test_user.id}",
            f"plot_threads:{chapter.story_id}:{test_user.id}",
            f"act_segmentation:{chapter.story_id}:{test_user.id}",
            f"contradictions:{chapter.story_id}:{test_user.id}",
            f"entities:{chapter.story_id}:{test_user.id}",
            f"suggestion:character:context-v2:{chapter.story_id}:{test_user.id}",
            f"suggestion:plot:context-v2:{chapter.story_id}:{test_user.id}",
            f"suggestion:structure:context-v2:{chapter.story_id}:{test_user.id}",
            f"suggestion:world:context-v2:{chapter.story_id}:{test_user.id}"
        ]

        for key in keys:
            await fake_redis.set(key, "value")

        await chapter_service.update_chapter(
            chapter_id=chapter_with_enough_content.id,
            user_id=test_user.id,
            data=UpdateChapterRequest(
                published=False
            )
        )

        assert all(
            value is None
            for value in 
            [
                await fake_redis.get(key)
                for key in keys
            ]
        )

    async def test_threshold_on_big_change(
        self,
        fake_redis: FakeRedis,
        fake_queue: FakeQueue,
        published_chapter_with_enough_content: ChapterRow,
        chapter_service: ChapterService
    ):
        updated = await chapter_service.update_chapter(
            chapter_id=published_chapter_with_enough_content.id,
            user_id=published_chapter_with_enough_content.user_id,
            data=UpdateChapterRequest(
                content=lorem.words(1500)
            )
        )
        pending_key = f"chapter:extraction-pending:{published_chapter_with_enough_content.id}"
        key = await fake_redis.get(pending_key)
        assert key is not None


    async def test_threshold_on_little_change(
        self,
        fake_redis: FakeRedis,
        fake_queue: FakeQueue,
        published_chapter_with_enough_content: ChapterRow,
        chapter_service: ChapterService
    ):
        # seed baseline — this is what the last extraction saw
        baseline_key = f"chapter:baseline:{published_chapter_with_enough_content.id}"
        original_text = html_to_plain_text(published_chapter_with_enough_content.content or "")
        await fake_redis.set(baseline_key, original_text)

        await chapter_service.update_chapter(
            chapter_id=published_chapter_with_enough_content.id,
            user_id=published_chapter_with_enough_content.user_id,
            data=UpdateChapterRequest(
                content=(published_chapter_with_enough_content.content or "") + " little change"
            )
        )
        
        pending_key = f"chapter:extraction-pending:{published_chapter_with_enough_content.id}"
        assert await fake_redis.get(pending_key) is None



        