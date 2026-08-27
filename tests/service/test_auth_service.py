from datetime import timedelta

import pytest

from src.data.schemas.auth import AuthCredentials, ConnectionDetails, RegistrationData, UserResponse
from src.infrastructure.auth.password import verify_password
from src.infrastructure.exceptions import DatabaseError
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError, ConflictError, ForbiddenError, InternalError
from tests.service.mocks import FakeSessionRepository, FakeUserRepository
from tests.service.mocks.common import now


TEST_PASSWORD = "mypassword123@ABC"
CONNECTION = ConnectionDetails(
    ip_address="127.0.0.1",
    user_agent="pytest",
)


class TestRegistration:
    async def test_valid_registration_hashes_password(
        self,
        auth_service: AuthService,
        fake_user_repo: FakeUserRepository,
    ) -> None:
        registration = RegistrationData(
            username="new_user",
            email="new_user@example.com",
            password=TEST_PASSWORD,
        )

        result = await auth_service.register_user(registration)
        stored = await fake_user_repo.get_by_email(registration.email)

        assert result.email == registration.email
        assert stored is not None
        assert stored.password_hash != TEST_PASSWORD
        assert verify_password(TEST_PASSWORD, stored.password_hash) is True

    async def test_duplicate_email_is_rejected(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        registration = RegistrationData(
            username="different_name",
            email=test_user.email,
            password=TEST_PASSWORD,
        )

        with pytest.raises(ConflictError, match="already exists"):
            await auth_service.register_user(registration)

    async def test_repository_failure_does_not_create_partial_user(
        self,
        auth_service: AuthService,
        fake_user_repo: FakeUserRepository,
    ) -> None:
        fake_user_repo.create_error = DatabaseError(
            "create failed",
            RuntimeError("database internals"),
        )
        registration = RegistrationData(
            username="failed_user",
            email="failed_user@example.com",
            password=TEST_PASSWORD,
        )

        with pytest.raises(InternalError, match="database error"):
            await auth_service.register_user(registration)

        assert await fake_user_repo.get_by_email(registration.email) is None


class TestAuthentication:
    async def test_correct_password_authenticates(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        user = await auth_service.authenticate_user(
            AuthCredentials(email=test_user.email, password=TEST_PASSWORD)
        )

        assert user.id == test_user.id

    async def test_wrong_password_is_rejected(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        with pytest.raises(AuthError) as exc_info:
            await auth_service.authenticate_user(
                AuthCredentials(
                    email=test_user.email,
                    password="WrongPassword123!",
                )
            )

        assert exc_info.value.message == "Incorrect email or password. Please try again."

    async def test_missing_account_uses_same_failure_message_as_wrong_password(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        with pytest.raises(AuthError) as wrong_password:
            await auth_service.authenticate_user(
                AuthCredentials(
                    email=test_user.email,
                    password="WrongPassword123!",
                )
            )

        with pytest.raises(AuthError) as missing_account:
            await auth_service.authenticate_user(
                AuthCredentials(
                    email="missing@example.com",
                    password="WrongPassword123!",
                )
            )

        assert missing_account.value.message == wrong_password.value.message

    async def test_login_creates_session_for_authenticated_user(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
        fake_session_repo: FakeSessionRepository,
    ) -> None:
        user, session_id = await auth_service.login_user(
            AuthCredentials(email=test_user.email, password=TEST_PASSWORD),
            CONNECTION,
        )

        session = await fake_session_repo.get(session_id)

        assert user.id == test_user.id
        assert session is not None
        assert session.user_id == test_user.id
        assert session.ip_address == CONNECTION.ip_address
        assert session.user_agent == CONNECTION.user_agent


class TestSessions:
    async def test_valid_session_resolves_correct_user(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        session_id = await auth_service.create_session(test_user.id, CONNECTION)

        resolved = await auth_service.validate_session(session_id)

        assert resolved.id == test_user.id

    @pytest.mark.parametrize("session_id", ["", "missing-session"])
    async def test_invalid_session_is_rejected(
        self,
        auth_service: AuthService,
        session_id: str,
    ) -> None:
        with pytest.raises(ForbiddenError):
            await auth_service.validate_session(session_id)

    async def test_expired_session_is_rejected_and_deleted(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
        fake_session_repo: FakeSessionRepository,
    ) -> None:
        session_id = await auth_service.create_session(test_user.id, CONNECTION)
        session = await fake_session_repo.get(session_id)
        assert session is not None

        fake_session_repo.seed(
            session.model_copy(update={"expires_at": now() - timedelta(seconds=1)})
        )

        with pytest.raises(ForbiddenError, match="expired"):
            await auth_service.validate_session(session_id)

        assert await fake_session_repo.get(session_id) is None

    async def test_logout_revokes_session(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        session_id = await auth_service.create_session(test_user.id, CONNECTION)

        await auth_service.logout_user(session_id)

        with pytest.raises(ForbiddenError):
            await auth_service.validate_session(session_id)

    async def test_session_remains_bound_to_its_owner(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        other = await auth_service.register_user(
            RegistrationData(
                username="other_user",
                email="other_user@example.com",
                password=TEST_PASSWORD,
            )
        )
        other_session = await auth_service.create_session(other.id, CONNECTION)

        resolved = await auth_service.validate_session(other_session)

        assert resolved.id == other.id
        assert resolved.id != test_user.id

    async def test_orphaned_session_is_rejected(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
        fake_user_repo: FakeUserRepository,
    ) -> None:
        session_id = await auth_service.create_session(test_user.id, CONNECTION)
        fake_user_repo.remove(test_user.id)

        with pytest.raises(ForbiddenError, match="User does not exist"):
            await auth_service.validate_session(session_id)

    async def test_multiple_sessions_for_same_user_remain_valid(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
    ) -> None:
        first = await auth_service.create_session(test_user.id, CONNECTION)
        second = await auth_service.create_session(test_user.id, CONNECTION)

        assert first != second
        assert (await auth_service.validate_session(first)).id == test_user.id
        assert (await auth_service.validate_session(second)).id == test_user.id

    async def test_session_creation_failure_is_safe_and_leaves_no_session(
        self,
        auth_service: AuthService,
        test_user: UserResponse,
        fake_session_repo: FakeSessionRepository,
    ) -> None:
        fake_session_repo.create_error = DatabaseError(
            "session create failed",
            RuntimeError("database internals"),
        )

        with pytest.raises(InternalError, match="database error"):
            await auth_service.create_session(test_user.id, CONNECTION)

        assert fake_session_repo._sessions == {}
