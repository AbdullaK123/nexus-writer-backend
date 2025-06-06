from fastapi import APIRouter, Request, Response, Depends, Cookie
from app.schemas.auth import UserResponse, RegistrationData, AuthCredentials
from app.models import User
from app.providers.auth import AuthProvider, get_auth_provider, get_current_user

user_controller = APIRouter(prefix='/auth')

@user_controller.post('/register', response_model=UserResponse)
async def register_user(
    request: Request, 
    registration_data: RegistrationData,
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> UserResponse:
    return await auth_provider.register_user(registration_data)


@user_controller.post('/login', response_model=UserResponse)
async def login_user(
    request: Request,
    response: Response,
    credentials: AuthCredentials,
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> UserResponse:
    return await auth_provider.login_user(
        request,
        response,
        credentials
    )

@user_controller.post('/logout')
async def logout_user(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    session_id: str = Cookie(),
    auth_provider: AuthProvider = Depends(get_auth_provider)
) -> dict:
    print(session_id)
    await auth_provider.logout_user(session_id)
    response.delete_cookie("session_id")
    return {'message': 'You have succesfully logged out'}

@user_controller.get('/me', response_model=UserResponse)
async def get_active_user(
    request: Request,
    user: User = Depends(get_current_user)
) -> UserResponse:
    return UserResponse(
        username=user.username,
        email=user.email,
        profile_img=user.profile_img
    )
