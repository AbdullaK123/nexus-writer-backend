from typing import Optional
from datetime import datetime, timedelta, timezone

from loguru import logger

from src.infrastructure.config import config
from src.data.models import User, Session
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


async def get_user_by_email(email: str) -> Optional[User]:
    return await User.filter(email=email).first()


@handle_service_errors
async def authenticate_user(credentials: AuthCredentials) -> User:
    user = await get_user_by_email(credentials.email)

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
    user_id: str, connection_details: ConnectionDetails
) -> str:
    session_id = generate_session_id()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=config.auth.session_ttl_days
    )

    await Session.create(
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
async def validate_session(session_id: str) -> Optional[User]:
    if not session_id:
        logger.warning("session.validate_failed.missing_session_id")
        raise ForbiddenError("Your session is invalid. Please log in again.")

    session = await Session.filter(session_id=session_id).first()

    if not session:
        logger.warning("session.validate_failed.not_found")
        raise ForbiddenError("Your session has expired. Please log in again.")

    if session.expires_at < datetime.now(timezone.utc):
        logger.warning("session.validate_failed.expired", user_id=session.user_id)
        await session.delete()
        raise ForbiddenError("Your session has expired. Please log in again.")

    user_id = session.user_id

    if not user_id:
        logger.warning("session.validate_failed.no_user_id")
        raise ForbiddenError("Your session is invalid. Please log in again.")

    user = await User.filter(id=user_id).first()

    if user is None:
        raise ForbiddenError("User does not exist")

    set_user_id(user.id)

    return user


@handle_service_errors
async def logout_user(session_id: str) -> None:
    if not session_id:
        return

    session = await Session.filter(session_id=session_id).first()

    if session:
        await session.delete()
        logger.info("session.deleted", user_id=session.user_id)
    else:
        logger.warning("session.logout_failed.not_found")


@handle_service_errors
async def login_user(
    credentials: AuthCredentials, connection_details: ConnectionDetails
) -> tuple[UserResponse, str]:
    user = await authenticate_user(credentials)
    session_id = await create_session(user.id, connection_details=connection_details)
    logger.info("auth.user_logged_in", user_id=str(user.id))
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        profile_img=user.profile_img,
    ), session_id


@handle_service_errors
async def register_user(registration_data: RegistrationData) -> UserResponse:
    user = await get_user_by_email(registration_data.email)

    if user:
        logger.warning(
            "auth.register_failed.duplicate_email",
            email=registration_data.email,
        )
        raise ConflictError(
            "An account with this email already exists. Try logging in instead."
        )

    user_to_create = await User.create(
        username=registration_data.username,
        email=registration_data.email,
        password_hash=hash_password(registration_data.password),
        profile_img=registration_data.profile_img,
    )
    logger.info("auth.user_registered", user_id=str(user_to_create.id))

    return UserResponse(
        id=str(user_to_create.id),
        username=registration_data.username,
        email=registration_data.email,
        profile_img=registration_data.profile_img,
    )
