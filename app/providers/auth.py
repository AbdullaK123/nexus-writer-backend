from app.config.settings import app_config
from app.core.database import get_db
from app.models import User, Session
from app.schemas.auth import RegistrationData, UserResponse, AuthCredentials, ConnectionDetails
from app.core.security import (
    hash_password,
    verify_password,
    generate_session_id,
    encrypt_session_data,
    decrypt_session_data
)
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from sqlmodel import select
from fastapi import status, Cookie, Response, Request, Depends
from typing import Optional, Union
from datetime import datetime, timedelta


class AuthProvider:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:  
        query = select(User).where(User.email == email)
        user = (await self.db.execute(query)).scalar_one_or_none()
        return user
    

    async def authenticate_user(self, credentials: AuthCredentials) -> User:
        user = await self.get_user_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Credentials"
            )
        
        return user
    

    async def create_session(self, user_id: str, connection_details: ConnectionDetails) -> Union[bytes, str]:

        # create session id and expiry time
        session_id = generate_session_id()
        expires_at = datetime.utcnow() + timedelta(days=1)

        # create record in db
        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=connection_details.ip_address,
            user_agent=connection_details.user_agent
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # encypt and set the cookie
        encypted_cookie = encrypt_session_data({'session_id': session_id})

        return encypted_cookie
    
    async def validate_session(self, encrypted_cookie_data: Union[bytes, str]) -> Optional[User]:

        decrypted_cookie = decrypt_session_data(encrypted_cookie_data)
        if not decrypted_cookie or 'session_id' not in decrypted_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid session"
            )
        
        
        session_query = select(Session).where(Session.session_id == decrypted_cookie.get('session_id'))

        session = (await self.db.execute(session_query)).scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Invalid session"
            )

        if session.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session expired"
            )
        
        user_id = session.user_id

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid session"
            )
        
        user_query = select(User).where(User.id == user_id)
        user = (await self.db.execute(user_query)).scalar_one_or_none()

        return user
    
    async def logout_user(self, encrypted_cookie_data: Union[bytes, str]) -> None:
        decrypted_cookie = decrypt_session_data(encrypted_cookie_data)

        if decrypted_cookie and 'session_id' in decrypted_cookie:

            session_query = select(Session).where(Session.session_id == decrypted_cookie.get('session_id'))

            session = (await self.db.execute(session_query)).scalar_one_or_none()

            if session:
                await self.db.delete(session)
                await self.db.commit()
    
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
            secure=(app_config.env == 'prod')
        )
        return UserResponse(
            username=user.username,
            email=user.email,
            profile_img=user.profile_img
        )


    async def register_user(self, registration_data: RegistrationData) -> UserResponse:

        user = await self.get_user_by_email(registration_data.email)

        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with that email already exists"
            )

        user_to_create = User(
            username=registration_data.username,
            email=registration_data.email,
            password_hash=hash_password(registration_data.password),
            profile_img=registration_data.profile_img
        )
        self.db.add(user_to_create)
        await self.db.commit()
        await self.db.refresh(user_to_create)


        return UserResponse(
            username=registration_data.username,
            email=registration_data.email,
            profile_img=registration_data.profile_img
        )



def get_auth_provider(db: AsyncSession = Depends(get_db)):
    return AuthProvider(db)

async def get_current_user(
    session_id: Union[bytes, str] = Cookie(..., alias='session_id'),
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> Optional[User]:
    return await auth_provider.validate_session(session_id)