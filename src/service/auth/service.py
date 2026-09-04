from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
from loguru import logger
import json
from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.schemas.chapter import ChapterListItem
from src.infrastructure.config import config as app_config
from src.data.repositories import UserRepository, SessionRepository
from src.data.schemas import UserRow
from src.data.schemas.auth import (
    DashboardResponse,
    Notification,
    OAuthUserRow,
    RegistrationData,
    SettingsPayload,
    StoryNavigationResponse,
    StoryNavigationRow,
    UserNavigationResponse,
    UserNavigationRow,
    UserResponse,
    AuthCredentials,
    ConnectionDetails,
)
from src.infrastructure.auth.password import hash_password, verify_password
from src.infrastructure.auth.session import generate_session_id
from src.infrastructure.redis.pubsub import RedisPubSub
from src.service.auth.templates.email import RESET_TEMPLATE, VERIFICATION_TEMPLATE
from src.service.exceptions import AuthError, ForbiddenError, ConflictError, InternalError, NotFoundError
from src.service.utils.decorators import handle_service_errors, handle_service_errors_stream
from src.shared.utils.correlation import set_user_id
import asyncpg
import resend
from resend.exceptions import ResendError


class AuthService:
    DUMMY_HASH = hash_password("password")

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        auth_token_repo: AuthTokenRepository,
        pubsub: RedisPubSub
    ):
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._auth_token_repo = auth_token_repo
        self._pubsub = pubsub

    @handle_service_errors
    async def authenticate_user(self, credentials: AuthCredentials) -> UserRow:
        user = await self._user_repo.get_by_email(credentials.email)
        password_hash = (
            user.password_hash
            if user is not None and user.password_hash is not None
            else self.DUMMY_HASH
        )
        password_valid = verify_password(credentials.password, password_hash)
        if user is None or user.password_hash is None or not password_valid:
            logger.warning("auth.login_failed.invalid_credentials", email=credentials.email)
            raise AuthError("Incorrect email or password. Please try again.")
        logger.info("auth.login_succeeded", user_id=str(user.id))
        return user

    @handle_service_errors
    async def create_session(self, user_id: str, connection_details: ConnectionDetails) -> str:
        session_id = generate_session_id()
        expires_at = datetime.now(timezone.utc) + timedelta(days=app_config.auth.session_ttl_days)
        await self._session_repo.create(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=connection_details.ip_address,
            user_agent=connection_details.user_agent,
        )
        logger.info("session.created", user_id=user_id, expires_at=str(expires_at))
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
            logger.info("session.deleted")
        else:
            logger.warning("session.logout_failed.not_found")

    @handle_service_errors
    async def get_or_create_oauth_account(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        name: str,
        email_verified: bool,
    ) -> OAuthUserRow:
        if not email_verified:
            raise AuthError("OAuth provider did not verify the email address.")

        canonical_email = email.strip().casefold()
        lock_keys = sorted((
            f"oauth:account:{provider}:{provider_user_id}",
            f"oauth:email:{canonical_email}",
        ))
        async with self._user_repo.pool.acquire() as conn:
            async with conn.transaction():
                for lock_key in lock_keys:
                    await conn.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                        lock_key,
                    )
                account = await self._user_repo.get_oauth_account(
                    provider=provider,
                    provider_user_id=provider_user_id,
                    executor=conn,
                )
                if account is not None:
                    await self._user_repo.verify_user(account.user_id, executor=conn)
                    return account

                user = await self._user_repo.get_by_email(canonical_email, executor=conn)
                if user is None:
                    user = await self._user_repo.create(
                        username=name,
                        email=canonical_email,
                        password_hash=None,
                        profile_img=None,
                        verified=True,
                        executor=conn,
                    )
                elif not user.email_verified:
                    await self._user_repo.verify_user(user.id, executor=conn)

                return await self._user_repo.create_oauth(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    executor=conn,
                )

    @handle_service_errors
    async def login_user(
        self,
        credentials: AuthCredentials,
        connection_details: ConnectionDetails,
    ) -> tuple[UserResponse, str]:
        user = await self.authenticate_user(credentials)
        session_id = await self.create_session(user.id, connection_details=connection_details)
        logger.info(
            "auth.user_logged_in",
            user_id=str(user.id),
            ip_address=str(connection_details.ip_address),
            user_agent=str(connection_details.user_agent),
        )
        return UserResponse.from_user_row(user), session_id

    @handle_service_errors
    async def register_user(self, registration_data: RegistrationData) -> UserResponse:
        existing = await self._user_repo.get_by_email(registration_data.email)
        if existing:
            logger.warning("auth.register_failed.duplicate_email", email=registration_data.email)
            raise ConflictError(
                "An account with this email already exists. Try logging in instead."
            )
        try:
            user = await self._user_repo.create(
                username=registration_data.username,
                email=registration_data.email,
                password_hash=hash_password(registration_data.password),
                profile_img=registration_data.profile_img,
            )
        except asyncpg.UniqueViolationError:
            raise ConflictError("A user with that username or email already exists.")
        logger.info("auth.user_registered", user_id=str(user.id))
        try:
            await self.send_verification_email(user.id)
        except InternalError as exc:
            logger.error(
                "auth.registration_verification_email_failed",
                user_id=user.id,
                error=str(exc),
            )
        return UserResponse.from_user_row(user)

    @handle_service_errors
    async def cleanup_expired_sessions(self) -> None:
        total_deleted = await self._session_repo.delete_expired()
        if total_deleted > 0:
            logger.info("session.cleanup_complete", sessions_deleted=total_deleted)

    @handle_service_errors
    async def get_dashboard(self, user_id: str) -> DashboardResponse:
        kpis, last_three_chapters = await self._user_repo.get_dashboard(user_id=user_id)
        return DashboardResponse(
            total_words=kpis["total_words"],
            total_stories=kpis["total_stories"],
            chapters_total=kpis["chapters_total"],
            chapters_published=kpis["chapters_published"],
            scenes_tracked=kpis["scenes_tracked"],
            streak_days=kpis["streak_days"],
            jump_back_in=[
                ChapterListItem(
                    story_id=item["story_id"],
                    chapter_id=item["chapter_id"],
                    chapter_number=item["chapter_number"],
                    word_count=item["word_count"],
                    story_title=item["story_title"],
                    chapter_title=item["chapter_title"],
                    published=item["published"],
                    updated_at=item["updated_at"],
                )
                for item in last_three_chapters
            ],
        )

    @staticmethod
    def _sse_frame(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    @handle_service_errors_stream
    async def stream_notifications(self, user_id: str) -> AsyncIterator[str]:
        try:
            async for notification in self._pubsub.listen(
                f"notifications:{user_id}", Notification
            ):
                yield self._sse_frame("notification", notification.model_dump(mode='json'))
        except Exception:
            yield self._sse_frame(
                "error", {"code": "INTERNAL", "message": "Internal server error"}
            )
            return
        yield self._sse_frame("done", {})

    @handle_service_errors
    async def get_editor_links(self, user_id: str) -> UserNavigationResponse:
        rows = await self._user_repo.get_editor_link_params(user_id=user_id)
        return UserNavigationResponse(
            links=[
                UserNavigationRow(
                    chapter_id=row[1],
                    story_id=row[0],
                    chapter_number=row[2],
                    label=row[3]
                )
                for row in rows
            ]
        )

    @handle_service_errors
    async def get_chat_links(self, user_id: str) -> StoryNavigationResponse:
        rows = await self._user_repo.get_chat_link_params(user_id=user_id)
        return StoryNavigationResponse(
            links=[StoryNavigationRow(story_id=row[0], title=row[1]) for row in rows]
        )

    @handle_service_errors
    async def update_settings(self, user_id: str, payload: SettingsPayload) -> UserResponse:
        row = await self._user_repo.update_settings(
            user_id, payload.model_dump(exclude={"kind"})
        )
        if row is None:
            raise NotFoundError("User not found")
        return UserResponse.from_user_row(row)

    @handle_service_errors
    async def send_password_reset_email(self, email: str) -> None:
        user = await self._user_repo.get_by_email(email)
        if user is None or not user.email_verified:
            return
        token = await self._auth_token_repo.create(
            user_id=user.id, purpose='password_reset'
        )
        reset_url = f"{app_config.auth.frontend_base_url}/reset-password?token={token}"
        try:
            await resend.Emails.send_async({
                "from": "noreply@nexuswriter.net",
                "to": user.email,
                "subject": "Reset your password",
                "html": RESET_TEMPLATE.render(
                    reset_url=reset_url,
                    expires_in_minutes=app_config.auth.auth_token_ttl_mins,
                ),
            })
        except ResendError as err:
            logger.error(
                "auth.password_reset_email_failed",
                user_id=user.id,
                error=str(err),
            )
            return

    @handle_service_errors
    async def reset_password(self, token: str, new_password: str) -> None:
        new_password_hash = hash_password(new_password)
        token_row = None
        expired = False
        async with self._user_repo.pool.acquire() as conn:
            async with conn.transaction():
                token_row = await self._auth_token_repo.consume(
                    token=token,
                    purpose='password_reset',
                    executor=conn,
                )
                if token_row is not None:
                    expired = token_row.expires_at < datetime.now(timezone.utc)
                    if not expired:
                        await self._user_repo.update_password(
                            token_row.user_id,
                            new_password_hash,
                            executor=conn,
                        )
                        await self._session_repo.delete_all(
                            token_row.user_id,
                            executor=conn,
                        )
        if token_row is None:
            raise AuthError("Invalid or already used password reset token.")
        if expired:
            raise AuthError("Token has expired.")

    @handle_service_errors
    async def send_verification_email(self, user_id: str) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if user.email_verified:
            return
        token = await self._auth_token_repo.create(
            user_id=user.id, purpose='email_verification'
        )
        verification_url = (
            f"{app_config.auth.api_base_url}/api/auth/tokens/verify?token={token}"
        )
        try:
            await resend.Emails.send_async({
                "from": "noreply@nexuswriter.net",
                "to": user.email,
                "subject": "Verify your email",
                "html": VERIFICATION_TEMPLATE.render(
                    verification_url=verification_url,
                    expires_in_minutes=app_config.auth.auth_token_ttl_mins
                )
            })
        except ResendError as err:
            logger.error(
                "auth.verification_email_failed",
                user_id=user.id,
                error=str(err),
            )
            raise InternalError("Failed to send verification email.")

    @handle_service_errors
    async def verify_email(self, token: str) -> None:
        token_row = None
        expired = False
        async with self._user_repo.pool.acquire() as conn:
            async with conn.transaction():
                token_row = await self._auth_token_repo.consume(
                    token=token,
                    purpose='email_verification',
                    executor=conn,
                )
                if token_row is not None:
                    expired = token_row.expires_at < datetime.now(timezone.utc)
                    if not expired:
                        await self._user_repo.verify_user(
                            token_row.user_id,
                            executor=conn,
                        )
        if token_row is None:
            raise AuthError("Invalid or already used verification token.")
        if expired:
            raise AuthError("Token has expired.")
