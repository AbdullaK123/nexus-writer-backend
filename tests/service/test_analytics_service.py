
from src.data.schemas.auth import RegistrationData
from src.data.schemas.enums import StoryStatus
from src.data.schemas.story import CreateStoryRequest, UpdateStoryRequest
from src.infrastructure.exceptions import DatabaseError
from src.service.auth.service import AuthService
from src.service.exceptions import ConflictError, NotFoundError, ServiceError
from src.service.story.service import StoryService
import pytest
from tests.service.mocks import FakeStoryRepository


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
    # but update will return None — simulating deletion between the two calls
    fake_story_repo.force_update_none = True

    with pytest.raises(NotFoundError, match="may have been deleted"):
        await story_service.update_story(
            user_id=user.id,
            story_id=list(fake_story_repo._stories.values())[0].id,
            update_info=UpdateStoryRequest(title="New title")
        )
    