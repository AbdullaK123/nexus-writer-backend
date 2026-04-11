from src.infrastructure.config import settings, config
from src.data.models import User, Session
from src.data.schemas.auth import RegistrationData, UserResponse, AuthCredentials, ConnectionDetails
from src.infrastructure.auth.password import hash_password, verify_password
from src.infrastructure.auth.session import generate_session_id, encrypt_session_data, decrypt_session_data
from src.service.exceptions import AuthError, ForbiddenError, ConflictError
from fastapi import status, Cookie, Response, Request, Depends
from dependency_injector.wiring import inject, Provide
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
from loguru import logger
from src.shared.utils.logging_context import context_logger, set_user_id


class AuthService:

    async def get_user_by_email(self, email: str) -> Optional[User]:  
        return await User.filter(email=email).first()
    

    async def authenticate_user(self, credentials: AuthCredentials) -> User:
        user = await self.get_user_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            context_logger(db_operation=True).warning(
                "Authentication failed for email={email}",
                email=credentials.email,
            )
            raise AuthError("Incorrect email or password. Please try again.")
        
        context_logger(db_operation=True).info(
            "Authentication succeeded for user_id={user_id}",
            user_id=(user.id if user else None),
        )
        return user
    

    async def create_session(self, user_id: str, connection_details: ConnectionDetails) -> Union[bytes, str]:

        # create session id and expiry time
        session_id = generate_session_id()
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)

        # create record in db
        await Session.create(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=connection_details.ip_address,
            user_agent=connection_details.user_agent
        )
        context_logger(db_operation=True).info(
            "Session created user_id={user_id} session_id={session_id}",
            user_id=user_id,
            session_id=session_id,
        )
        
        # encypt and set the cookie
        encypted_cookie = encrypt_session_data({'session_id': session_id})

        return encypted_cookie
    
    async def validate_session(self, encrypted_cookie_data: Union[bytes, str]) -> Optional[User]:

        if isinstance(encrypted_cookie_data, bytes):
            encrypted_cookie_data = encrypted_cookie_data.decode('utf-8')

        decrypted_cookie = decrypt_session_data(encrypted_cookie_data)
        if not decrypted_cookie or 'session_id' not in decrypted_cookie:
            context_logger(db_operation=True).warning("Missing or malformed session cookie")
            raise ForbiddenError("Your session is invalid. Please log in again.")
        
        session = await Session.filter(
            session_id=decrypted_cookie.get('session_id')
        ).first()

        if not session:
            context_logger(db_operation=True).warning("Session not found in DB")
            raise ForbiddenError("Your session has expired. Please log in again.")

        if session.expires_at < datetime.now(timezone.utc):
            context_logger(db_operation=True).warning("Session expired user_id={user_id}", user_id=session.user_id)
            raise ForbiddenError("Your session has expired. Please log in again.")
        
        user_id = session.user_id

        if not user_id:
            context_logger(db_operation=True).warning("Session without user_id")
            raise ForbiddenError("Your session is invalid. Please log in again.")
        
        user = await User.filter(id=user_id).first()
        if user:
            set_user_id(user.id)

        return user
    
    async def logout_user(self, encrypted_cookie_data: Union[bytes, str]) -> None:
        decrypted_cookie = decrypt_session_data(encrypted_cookie_data)

        if decrypted_cookie and 'session_id' in decrypted_cookie:

            session = await Session.filter(
                session_id=decrypted_cookie.get('session_id')
            ).first()

            if session:
                await session.delete()
                context_logger(db_operation=True).info("Session deleted for user_id={user_id}", user_id=session.user_id)
            else:
                context_logger(db_operation=True).warning("Logout requested but session not found")
    
    async def login_user(self, request: Request, response: Response, credentials: AuthCredentials) -> UserResponse:
        user = await self.authenticate_user(credentials)
        ip_address = request.headers.get('X-Real-IP')
        user_agent = request.headers.get('User-Agent')
        connection_details = ConnectionDetails(ip_address=ip_address, user_agent=user_agent)
        encypted_cookie = await self.create_session(user.id, connection_details=connection_details)
        response.set_cookie(
            key='session_id',
            value=encypted_cookie,
            max_age=86400,
            httponly=True,
            samesite='lax',
            secure=(settings.env == 'prod')
        )
        context_logger(db_operation=True).info(
            "User logged in user_id={user_id}",
            user_id=user.id,
        )
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            profile_img=user.profile_img
        )


    async def register_user(self, registration_data: RegistrationData) -> UserResponse:

        user = await self.get_user_by_email(registration_data.email)

        if user:
            context_logger(db_operation=True).warning(
                "Registration attempted with duplicate email={email}",
                email=registration_data.email,
            )
            raise ConflictError("An account with this email already exists. Try logging in instead.")

        user_to_create = await User.create(
            username=registration_data.username,
            email=registration_data.email,
            password_hash=hash_password(registration_data.password),
            profile_img=registration_data.profile_img
        )
        context_logger(db_operation=True).info(
            "User registered user_id={user_id}",
            user_id=user_to_create.id,
        )

        return UserResponse(
            id=str(user_to_create.id),
            username=registration_data.username,
            email=registration_data.email,
            profile_img=registration_data.profile_img
        )


@inject
async def get_current_user(
    request: Request,
    session_id: Union[bytes, str] = Cookie(),
    auth_service: AuthService = Depends(Provide["auth_service"])
) -> Optional[User]:
    user = await auth_service.validate_session(session_id)
    # make user id available for logging middleware
    if user is not None:
        try:
            request.state.user_id = user.id  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            set_user_id(user.id)
        except Exception:
            pass
    return user