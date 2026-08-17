
from src.data.schemas.auth import RegistrationData
from src.data.schemas.enums import StoryStatus
from src.data.schemas.extraction import INSUFFICIENT_CONTEXT
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.infrastructure.exceptions import DatabaseError
from src.service.auth.service import AuthService
from src.service.chapter.service import ChapterService
from src.service.exceptions import ConflictError, NotFoundError, ServiceError
from src.service.story.service import StoryService
import pytest
from tests.service.mocks import FakeRedis, FakeStoryRepository, FakeSceneRepository, FakeAIProvider, FakeChapterRepository


async def test_create_story_duplicates(
    story_service: StoryService,
    auth_service: AuthService
):

    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )
    
    story = await story_service.create_story(
        user_id=user.id,
        story_info=CreateStoryRequest(
            title="Test story"
        )
    )

    with pytest.raises(ConflictError):
        story = await story_service.create_story(
            user_id=user.id,
            story_info=CreateStoryRequest(
                title="Test story"
            )
        )


async def test_create_story_infra_failure(
    story_service: StoryService,
    auth_service: AuthService,
    fake_story_repo: FakeStoryRepository
):

    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )

    fake_story_repo.error = DatabaseError("Connection lost")

    with pytest.raises(ServiceError):
        story = await story_service.create_story(
            user_id=user.id,
            story_info=CreateStoryRequest(
                title="Test story"
            )
        )


async def test_update_story_not_found_path(
    story_service: StoryService,
    auth_service: AuthService
):

    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )

    with pytest.raises(NotFoundError):
        story = await story_service.update_story(
            user_id=user.id,
            story_id="I don't exist",
            update_info=UpdateStoryRequest(
                title="Changed",
                status=StoryStatus.ON_HIATUS
            )
        )
    

async def test_update_story_deleted_between_get_and_update(
    story_service: StoryService,
    auth_service: AuthService,
    fake_story_repo: FakeStoryRepository,
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )

    await story_service.create_story(
        user_id=user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    # story exists — get will find it
    fake_story_repo.force_update_none = True

    with pytest.raises(NotFoundError, match="may have been deleted"):
        await story_service.update_story(
            user_id=user.id,
            story_id=list(fake_story_repo._stories.values())[0].id,
            update_info=UpdateStoryRequest(title="New title")
        )

async def test_update_story_status_change_invalidates_cache(
    story_service: StoryService,
    auth_service: AuthService,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )

    await story_service.create_story(
        user_id=user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    story = list(fake_story_repo._stories.values())[0]

    # seed cache keys that should be invalidated
    cache_keys = [
        f"pulse:{story.id}:{user.id}",
        f"act_segmentation:{story.id}:{user.id}",
        f"suggestion:character:context-v2:{story.id}:{user.id}",
        f"suggestion:plot:context-v2:{story.id}:{user.id}",
        f"suggestion:structure:context-v2:{story.id}:{user.id}",
        f"suggestion:world:context-v2:{story.id}:{user.id}",
    ]

    for key in cache_keys:
        await fake_redis.set(key, "cached_data")

    # status change: Ongoing → Complete
    await story_service.update_story(
        user_id=user.id,
        story_id=story.id,
        update_info=UpdateStoryRequest(status=StoryStatus.COMPLETE),
    )

    # all keys should be gone
    for key in cache_keys:
        assert await fake_redis.get(key) is None


async def test_update_story_no_status_change_preserves_cache(
    story_service: StoryService,
    auth_service: AuthService,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="test@example.com",
            password="test_password_123@ABC"
        )
    )

    await story_service.create_story(
        user_id=user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    story = list(fake_story_repo._stories.values())[0]

    cache_keys = [
        f"pulse:{story.id}:{user.id}",
        f"act_segmentation:{story.id}:{user.id}",
        f"suggestion:character:context-v2:{story.id}:{user.id}",
        f"suggestion:plot:context-v2:{story.id}:{user.id}",
        f"suggestion:structure:context-v2:{story.id}:{user.id}",
        f"suggestion:world:context-v2:{story.id}:{user.id}",
    ]

    for key in cache_keys:
        await fake_redis.set(key, "cached_data")

    # title change only — no status change
    await story_service.update_story(
        user_id=user.id,
        story_id=story.id,
        update_info=UpdateStoryRequest(title="New title"),
    )

    # all keys should still be there
    for key in cache_keys:
        assert await fake_redis.get(key) == "cached_data"


async def test_delete_story_not_found_path(
    story_service: StoryService,
    auth_service: AuthService
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="email@test.com",
            password="testpassword123@ABC"
        )
    )

    with pytest.raises(NotFoundError):
        result = await story_service.delete_story(
            user_id=user.id,
            story_id="I don't exist"
        )


async def test_get_pulse_not_found_path(
    story_service: StoryService,
    auth_service: AuthService
):

    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="email@test.com",
            password="testpassword123@ABC"
        )
    )

    with pytest.raises(NotFoundError):
        result = await story_service.get_pulse(
            user_id=user.id,
            story_id="I don't exist"
        )


async def test_get_pulse_insufficient_context_path(
    story_service: StoryService,
    auth_service: AuthService,
    fake_story_repo: FakeStoryRepository,
    fake_scene_repo: FakeSceneRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_provider: FakeAIProvider
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="email@test.com",
            password="testpassword123@ABC"
        )
    )

    story = await fake_story_repo.create(user_id=user.id, title="Test Story")

    chapter = await fake_chapter_repo.create(story_id=story.id, user_id=user.id, title="test chapter", content="test content", word_count=2)

    await fake_scene_repo.replace_for_chapter(
        chapter_id=chapter.id, 
        story_id=story.id, 
        user_id=user.id, 
        scenes=[
            "scene_1",
            "scene_2"
        ]
    )

    result = await story_service.get_pulse(
        user_id=user.id,
        story_id=story.id
    )

    assert result == INSUFFICIENT_CONTEXT and fake_provider.call_count == 0


async def test_get_pulse_cache_hit_path(
    story_service: StoryService,
    auth_service: AuthService,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
    fake_provider: FakeAIProvider
):
    user = await auth_service.register_user(
        registration_data=RegistrationData(
            username="test_user",
            email="email@test.com",
            password="testpassword123@ABC"
        )
    )

    story = await fake_story_repo.create(user_id=user.id, title="Test Story")

    await fake_redis.set(f"pulse:{story.id}:{user.id}", INSUFFICIENT_CONTEXT.model_dump_json())

    result = await story_service.get_pulse(user_id=user.id, story_id=story.id)

    assert result is not None and fake_provider.call_count == 0