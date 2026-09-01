import pytest
from uuid_extensions import uuid7str

from src.data.schemas.auth import AuthCredentials, UserRow
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError
from tests.service.mocks import FakeUserRepository
from tests.service.mocks.common import now


async def test_oauth_only_account_password_login_is_rejected_without_crashing(
    auth_service: AuthService,
    fake_user_repo: FakeUserRepository,
) -> None:
    oauth_only_user = UserRow(
        id=uuid7str(),
        username="oauth_user",
        email="oauth-only@example.com",
        password_hash=None,
        profile_img=None,
        settings={},
        created_at=now(),
        updated_at=now(),
    )
    fake_user_repo.seed(oauth_only_user)

    with pytest.raises(AuthError) as exc_info:
        await auth_service.authenticate_user(
            AuthCredentials(
                email=oauth_only_user.email,
                password="WrongPassword123!",
            )
        )

    assert exc_info.value.message == "Incorrect email or password. Please try again."
