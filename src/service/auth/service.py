from src.infrastructure.config import settings, config
from src.data.models import User, Session
from src.data.schemas.auth import RegistrationData, UserResponse, AuthCredentials, ConnectionDetails
from src.infrastructure.auth.password import hash_password, verify_password
from src.infrastructure.auth.session import generate_session_id, encrypt_session_data, decrypt_session_data
from src.service.exceptions import AuthError, ForbiddenError, ConflictError
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE, set_user_id

log = get_layer_logger(LAYER_SERVICE)


class AuthService:

    async def get_user_by_email(self, email: str) -> Optional[User]:  
        return await User.filter(email=email).first()
    

    async def authenticate_user(self, credentials: AuthCredentials) -> User:
        user = await self.get_user_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            log.warning(
                "auth.login_failed: invalid credentials",
                email=credentials.email,
            )
            raise AuthError("Incorrect email or password. Please try again.")
        
        log.info(
            "auth.login_succeeded",
            user_id=str(user.id),
        )
        return user
    

    async def create_session(self, user_id: str, connection_details: ConnectionDetails) -> str:

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
        log.info(
            "session.created",
            user_id=user_id,
            session_id=session_id,
            expires_at=str(expires_at),
        )
        
        # encypt and set the cookie
        encypted_cookie = encrypt_session_data({'session_id': session_id})

        return encypted_cookie
    
    async def validate_session(self, encrypted_cookie_data: Union[bytes, str]) -> Optional[User]:

        if isinstance(encrypted_cookie_data, bytes):
            encrypted_cookie_data = encrypted_cookie_data.decode('utf-8')

        decrypted_cookie = decrypt_session_data(encrypted_cookie_data)
        if not decrypted_cookie or 'session_id' not in decrypted_cookie:
            log.warning("session.validate_failed: missing or malformed cookie")
            raise ForbiddenError("Your session is invalid. Please log in again.")
        
        session = await Session.filter(
            session_id=decrypted_cookie.get('session_id')
        ).first()

        if not session:
            log.warning("session.validate_failed: session not found in DB")
            raise ForbiddenError("Your session has expired. Please log in again.")

        if session.expires_at < datetime.now(timezone.utc):
            log.warning("session.validate_failed: expired", user_id=session.user_id)  # type: ignore[attr-defined]
            await session.delete()
            raise ForbiddenError("Your session has expired. Please log in again.")
        
        user_id = session.user_id  # type: ignore[attr-defined]

        if not user_id:
            log.warning("session.validate_failed: session has no user_id")
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
                log.info("session.deleted", user_id=session.user_id)  # type: ignore[attr-defined]
            else:
                log.warning("session.logout_failed: session not found")
    
    async def login_user(self, credentials: AuthCredentials, connection_details: ConnectionDetails) -> tuple[UserResponse, str]:
        user = await self.authenticate_user(credentials)
        encrypted_cookie = await self.create_session(user.id, connection_details=connection_details)
        log.info(
            "auth.user_logged_in",
            user_id=str(user.id),
        )
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            profile_img=user.profile_img
        ), encrypted_cookie


    async def register_user(self, registration_data: RegistrationData) -> UserResponse:

        user = await self.get_user_by_email(registration_data.email)

        if user:
            log.warning(
                "auth.register_failed: duplicate email",
                email=registration_data.email,
            )
            raise ConflictError("An account with this email already exists. Try logging in instead.")

        user_to_create = await User.create(
            username=registration_data.username,
            email=registration_data.email,
            password_hash=hash_password(registration_data.password),
            profile_img=registration_data.profile_img
        )
        log.info(
            "auth.user_registered",
            user_id=str(user_to_create.id),
        )

        return UserResponse(
            id=str(user_to_create.id),
            username=registration_data.username,
            email=registration_data.email,
            profile_img=registration_data.profile_img
        )