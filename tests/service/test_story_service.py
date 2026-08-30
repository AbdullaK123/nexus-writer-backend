
from src.data.schemas.auth import RegistrationData, UserResponse
from src.data.schemas.enums import StoryStatus
from src.data.schemas.extraction import INSUFFICIENT_CONTEXT, BookPulseResponse, PulseDimension
from src.data.schemas.scene import SceneRow
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.infrastructure.exceptions import DatabaseError, LLMServiceError
from src.service.auth.service import AuthService
from src.service.chapter.service import ChapterService
from src.service.exceptions import ConflictError, InternalError, NotFoundError, ServiceError
from src.service.story.service import StoryService
import pytest
from uuid_extensions import uuid7str
from datetime import datetime as dt
from tests.service.mocks import FakeRedis, FakeStoryRepository, FakeSceneRepository, FakeAIProvider, FakeChapterRepository


async def test_create_story_duplicates(
    story_service: StoryService,
    test_user: UserResponse
):
    
    story = await story_service.create_story(
        user_id=test_user.id,
        story_info=CreateStoryRequest(
            title="Test story"
        )
    )

    with pytest.raises(ConflictError):
        story = await story_service.create_story(
            user_id=test_user.id,
            story_info=CreateStoryRequest(
                title="Test story"
            )
        )


async def test_create_story_infra_failure(
    story_service: StoryService,
    fake_story_repo: FakeStoryRepository,
    test_user: UserResponse
):

    fake_story_repo.error = DatabaseError("Connection lost")

    with pytest.raises(ServiceError):
        story = await story_service.create_story(
            user_id=test_user.id,
            story_info=CreateStoryRequest(
                title="Test story"
            )
        )


async def test_update_story_not_found_path(
    story_service: StoryService,
    test_user: UserResponse
):

    with pytest.raises(NotFoundError):
        story = await story_service.update_story(
            user_id=test_user.id,
            story_id="I don't exist",
            update_info=UpdateStoryRequest(
                title="Changed",
                status=StoryStatus.ON_HIATUS
            )
        )
    

async def test_update_story_deleted_between_get_and_update(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
):
   
    await story_service.create_story(
        user_id=test_user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    # story exists — get will find it
    fake_story_repo.force_update_none = True

    with pytest.raises(NotFoundError, match="may have been deleted"):
        await story_service.update_story(
            user_id=test_user.id,
            story_id=list(fake_story_repo._stories.values())[0].id,
            update_info=UpdateStoryRequest(title="New title")
        )

async def test_update_story_status_change_invalidates_cache(
    story_service: StoryService,
    test_user: UserResponse,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
):

    await story_service.create_story(
        user_id=test_user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    story = list(fake_story_repo._stories.values())[0]

    # seed cache keys that should be invalidated
    cache_keys = [
        f"pulse:{story.id}:{test_user.id}",
        f"act_segmentation:{story.id}:{test_user.id}",
        f"suggestion:character:context-v2:{story.id}:{test_user.id}",
        f"suggestion:plot:context-v2:{story.id}:{test_user.id}",
        f"suggestion:structure:context-v2:{story.id}:{test_user.id}",
        f"suggestion:world:context-v2:{story.id}:{test_user.id}",
    ]

    for key in cache_keys:
        await fake_redis.set(key, "cached_data")

    # status change: Ongoing → Complete
    await story_service.update_story(
        user_id=test_user.id,
        story_id=story.id,
        update_info=UpdateStoryRequest(status=StoryStatus.COMPLETE),
    )

    # all keys should be gone
    for key in cache_keys:
        assert await fake_redis.get(key) is None


async def test_update_story_no_status_change_preserves_cache(
    story_service: StoryService,
    test_user: UserResponse,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
):

    await story_service.create_story(
        user_id=test_user.id,
        story_info=CreateStoryRequest(title="Test story")
    )

    story = list(fake_story_repo._stories.values())[0]

    cache_keys = [
        f"pulse:{story.id}:{test_user.id}",
        f"act_segmentation:{story.id}:{test_user.id}",
        f"suggestion:character:context-v2:{story.id}:{test_user.id}",
        f"suggestion:plot:context-v2:{story.id}:{test_user.id}",
        f"suggestion:structure:context-v2:{story.id}:{test_user.id}",
        f"suggestion:world:context-v2:{story.id}:{test_user.id}",
    ]

    for key in cache_keys:
        await fake_redis.set(key, "cached_data")

    # title change only — no status change
    await story_service.update_story(
        user_id=test_user.id,
        story_id=story.id,
        update_info=UpdateStoryRequest(title="New title"),
    )

    # all keys should still be there
    for key in cache_keys:
        assert await fake_redis.get(key) == "cached_data"


async def test_delete_story_not_found_path(
    story_service: StoryService,
    test_user: UserResponse
):

    with pytest.raises(NotFoundError):
        result = await story_service.delete_story(
            user_id=test_user.id,
            story_id="I don't exist"
        )


async def test_get_pulse_not_found_path(
    story_service: StoryService,
    test_user: UserResponse
):
    with pytest.raises(NotFoundError):
        result = await story_service.get_pulse(
            user_id=test_user.id,
            story_id="I don't exist"
        )


async def test_get_pulse_insufficient_context_path(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_scene_repo: FakeSceneRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_provider: FakeAIProvider
):
    story = await fake_story_repo.create(user_id=test_user.id, title="Test Story")

    chapter = await fake_chapter_repo.create(story_id=story.id, user_id=test_user.id, title="test chapter", content="test content", word_count=2)

    await fake_scene_repo.replace_for_chapter(
        chapter_id=chapter.id, 
        story_id=story.id, 
        user_id=test_user.id, 
        scenes=[
            "scene_1",
            "scene_2"
        ]
    )

    result = await story_service.get_pulse(
        user_id=test_user.id,
        story_id=story.id
    )

    assert result == INSUFFICIENT_CONTEXT and fake_provider.call_count == 0


async def test_get_pulse_cache_hit_path(
    story_service: StoryService,
    test_user: UserResponse,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository,
    fake_provider: FakeAIProvider
):

    story = await fake_story_repo.create(user_id=test_user.id, title="Test Story")

    await fake_redis.set(f"pulse:{story.id}:{test_user.id}", INSUFFICIENT_CONTEXT.model_dump_json())

    result = await story_service.get_pulse(user_id=test_user.id, story_id=story.id)

    assert result is not None and fake_provider.call_count == 0


async def test_get_pulse_cache_poisoning_path(
    story_service: StoryService,
    test_user: UserResponse,
    fake_redis: FakeRedis,
    fake_story_repo: FakeStoryRepository
):
    
    story = await fake_story_repo.create(user_id=test_user.id, title="Test Story")
    cache_key = f"pulse:{story.id}:{test_user.id}"

    await fake_redis.set(cache_key, "I'm invalid data!")

    result = await story_service.get_pulse(user_id=test_user.id, story_id=story.id)

    assert result == INSUFFICIENT_CONTEXT
    assert await fake_redis.get(cache_key) is None


async def test_get_pulse_cache_llm_error_path(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_scene_repo: FakeSceneRepository,
    fake_provider: FakeAIProvider
):
    
    story = await fake_story_repo.create(user_id=test_user.id, title="Test Story")
    chapter = await fake_chapter_repo.create(story_id=story.id, user_id=test_user.id, title="Test chapter", content="content", word_count=1)
    await fake_story_repo.set_path_array(story.id, [chapter.id])

    for i in range(3):
        fake_scene_repo.seed(
            SceneRow(
                id=uuid7str(),
                story_id=story.id,
                user_id=test_user.id,
                chapter_id=chapter.id,
                position=i,
                start_quote="start",
                end_quote="end",
                description="content",
                pov="pov",
                word_count=3,
                tension="high",
                pacing="steady",
                mentioned_entities=["1", "2", "3"],
                tags=["1", "2", "3"],
                questions_raised=["1", "2", "3"],
                title="scene",
                created_at=dt.now(),
                updated_at=dt.now()
            )
        )

    fake_provider.error = LLMServiceError("KABOOM!")

    with pytest.raises(InternalError):
        await story_service.get_pulse(user_id=test_user.id, story_id=story.id)

async def test_format_scenes_chapter_not_in_path_array(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_chapter_repo: FakeChapterRepository,
    fake_scene_repo: FakeSceneRepository,
):

    story = await fake_story_repo.create(user_id=test_user.id, title="Test Story")
    chapter = await fake_chapter_repo.create(
        story_id=story.id, user_id=test_user.id,
        title="Test chapter", content="content", word_count=1
    )

    # path_array is empty — chapter exists but isn't in the canonical story path
    for i in range(3):
        fake_scene_repo.seed(
            SceneRow(
                id=uuid7str(), story_id=story.id, user_id=test_user.id,
                chapter_id=chapter.id, position=i,
                start_quote="s", end_quote="e", description="d",
                pov="p", word_count=3, tension="high", pacing="steady",
                mentioned_entities=[], tags=[], questions_raised=[],
                title="scene", created_at=dt.now(), updated_at=dt.now()
            )
        )

    result = await story_service.get_pulse(user_id=test_user.id, story_id=story.id)

    assert result == INSUFFICIENT_CONTEXT


async def test_normalize_pulse_evidence_invalid_chapters(
    story_service: StoryService
):

    pulse = PulseDimension(
            label="unavailable",
            headline="test",
            whats_working="test",
            whats_not_working=(
                "test"
                "test"
            ),
            evidence_chapters=[1, 2, 99],
        )

    normalized = story_service._normalize_pulse_evidence(pulse, {1, 2})

    assert normalized.evidence_chapters == [1, 2]