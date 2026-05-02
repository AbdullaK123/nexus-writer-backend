from datetime import datetime, timedelta, timezone

from loguru import logger

from src.infrastructure.config import config
from src.data.repositories import UserRepository, SessionRepository
from src.data.schemas import UserRow
from src.data.schemas.auth import (
    RegistrationData,
    UserResponse,
    AuthCredentials,
    ConnectionDetails,
)
from src.infrastructure.auth.password import hash_password, verify_password
from src.infrastructure.auth.session import generate_session_id
from src.service.exceptions import AuthError, ForbiddenError, ConflictError
from src.service.utils.decorators import handle_service_errors
from src.shared.utils.correlation import set_user_id


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
    ):
        self._user_repo = user_repo
        self._session_repo = session_repo

    @handle_service_errors
    async def authenticate_user(self, credentials: AuthCredentials) -> UserRow:
        user = await self._user_repo.get_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            logger.warning(
                "auth.login_failed.invalid_credentials",
                email=credentials.email,
            )
            raise AuthError("Incorrect email or password. Please try again.")

        logger.info("auth.login_succeeded", user_id=str(user.id))
        return user

    @handle_service_errors
    async def create_session(
        self,
        user_id: str,
        connection_details: ConnectionDetails,
    ) -> str:
        session_id = generate_session_id()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=config.auth.session_ttl_days
        )

        await self._session_repo.create(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=connection_details.ip_address,
            user_agent=connection_details.user_agent,
        )
        logger.info(
            "session.created",
            user_id=user_id,
            session_id=session_id,
            expires_at=str(expires_at),
        )

        return session_id

    @handle_service_errors
    async def validate_session(self, session_id: str) -> UserRow:
        if not session_id:
            logger.warning("session.validate_failed.missing_session_id")
            raise ForbiddenError("Your session is invalid. Please log in again.")

        session = await self._session_repo.get(session_id)

        if not session:
            logger.warning("session.validate_failed.not_found")
            raise ForbiddenError("Your session has expired. Please log in again.")

        if session.expires_at < datetime.now(timezone.utc):
            logger.warning("session.validate_failed.expired", user_id=session.user_id)
            await self._session_repo.delete(session_id)
            raise ForbiddenError("Your session has expired. Please log in again.")

        user = await self._user_repo.get_by_id(session.user_id)

        if user is None:
            raise ForbiddenError("User does not exist")

        set_user_id(user.id)

        return user

    @handle_service_errors
    async def logout_user(self, session_id: str) -> None:
        if not session_id:
            return

        deleted = await self._session_repo.delete(session_id)

        if deleted:
            logger.info("session.deleted", session_id=session_id)
        else:
            logger.warning("session.logout_failed.not_found")

    @handle_service_errors
    async def login_user(
        self,
        credentials: AuthCredentials,
        connection_details: ConnectionDetails,
    ) -> tuple[UserResponse, str]:
        user = await self.authenticate_user(credentials)
        session_id = await self.create_session(
            user.id, connection_details=connection_details
        )
        logger.info("auth.user_logged_in", user_id=str(user.id))
        return UserResponse.model_validate(user, from_attributes=True), session_id

    @handle_service_errors
    async def register_user(
        self, registration_data: RegistrationData,
    ) -> UserResponse:
        existing = await self._user_repo.get_by_email(registration_data.email)

        if existing:
            logger.warning(
                "auth.register_failed.duplicate_email",
                email=registration_data.email,
            )
            raise ConflictError(
                "An account with this email already exists. Try logging in instead."
            )

        user = await self._user_repo.create(
            username=registration_data.username,
            email=registration_data.email,
            password_hash=hash_password(registration_data.password),
            profile_img=registration_data.profile_img,
        )
        logger.info("auth.user_registered", user_id=str(user.id))

        return UserResponse.model_validate(user, from_attributes=True)

    @handle_service_errors
    async def cleanup_expired_sessions(self) -> None:
        """Worker-side cron task. Removes sessions past their expires_at."""
        total_deleted = await self._session_repo.delete_expired()

        if total_deleted > 0:
            logger.info("session.cleanup_complete", sessions_deleted=total_deleted)
