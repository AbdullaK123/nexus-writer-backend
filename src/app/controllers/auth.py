from fastapi import APIRouter, Request, Response, Depends, Cookie
from dependency_injector.wiring import inject, Provide
from src.data.schemas.auth import UserResponse, RegistrationData, AuthCredentials
from src.data.models import User
from src.service.auth.service import AuthService, get_current_user

user_controller = APIRouter(prefix='/auth')

@user_controller.post('/register', response_model=UserResponse)
@inject
async def register_user(
    request: Request, 
    registration_data: RegistrationData,
    auth_service: AuthService = Depends(Provide["auth_service"])
) -> UserResponse:
    return await auth_service.register_user(registration_data)


@user_controller.post('/login', response_model=UserResponse)
@inject
async def login_user(
    request: Request,
    response: Response,
    credentials: AuthCredentials,
    auth_service: AuthService = Depends(Provide["auth_service"])
) -> UserResponse:
    return await auth_service.login_user(
        request,
        response,
        credentials
    )

@user_controller.post('/logout')
@inject
async def logout_user(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    session_id: str = Cookie(),
    auth_service: AuthService = Depends(Provide["auth_service"])
) -> dict:
    await auth_service.logout_user(session_id)
    response.delete_cookie("session_id")
    return {'message': 'You have succesfully logged out'}

@user_controller.get('/me', response_model=UserResponse)
async def get_active_user(
    request: Request,
    user: User = Depends(get_current_user)
) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        profile_img=user.profile_img
    )
