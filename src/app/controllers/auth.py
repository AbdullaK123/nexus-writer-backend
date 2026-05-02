from fastapi import APIRouter, Request, Response, Depends, Cookie

from src.data.schemas.auth import (
    UserResponse,
    RegistrationData,
    AuthCredentials,
    ConnectionDetails,
)
from src.data.schemas import UserRow
from src.app.dependencies import get_current_user, get_auth_service
from src.infrastructure.config import settings, config as app_config
from src.service.auth import AuthService

user_controller = APIRouter(prefix="/auth")


@user_controller.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    registration_data: RegistrationData,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return await auth_service.register_user(registration_data)


@user_controller.post("/login", response_model=UserResponse)
async def login_user(
    request: Request,
    response: Response,
    credentials: AuthCredentials,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    connection_details = ConnectionDetails(
        ip_address=request.headers.get("X-Real-IP"),
        user_agent=request.headers.get("User-Agent"),
    )
    user_response, session_id = await auth_service.login_user(
        credentials, connection_details
    )

    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=app_config.auth.cookie_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=(settings.env == "prod"),
    )
    return user_response


@user_controller.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    user: UserRow = Depends(get_current_user),
    session_id: str = Cookie(),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    await auth_service.logout_user(session_id)
    response.delete_cookie("session_id")
    return {"message": "You have succesfully logged out"}


@user_controller.get("/me", response_model=UserResponse)
async def get_active_user(
    request: Request, user: UserRow = Depends(get_current_user)
) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)
