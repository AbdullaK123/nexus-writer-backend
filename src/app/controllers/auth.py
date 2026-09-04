from fastapi import APIRouter, Request, Response, Depends, Cookie
from fastapi.responses import RedirectResponse, StreamingResponse
from src.data.schemas.auth import (
    DashboardResponse,
    ForgottenPasswordRequest,
    ResetPasswordRequest,
    SettingsPayload,
    StoryNavigationResponse,
    UserNavigationResponse,
    UserResponse,
    RegistrationData,
    AuthCredentials,
    ConnectionDetails,
)
from src.data.schemas import UserRow
from src.app.dependencies import get_current_user, get_auth_service
from src.infrastructure.config import settings, config as app_config
from src.service.auth import AuthService
from src.shared.text_types import AuthTokenInput
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request as StarletteRequest

from src.service.exceptions import AuthError

user_controller = APIRouter(prefix="/auth")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


@user_controller.get("/google/login")
async def google_login(request: StarletteRequest):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@user_controller.get("/google/callback")
async def google_callback(
    request: StarletteRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token['userinfo']

    account = await auth_service.get_or_create_oauth_account(
        provider="google",
        provider_user_id=userinfo['sub'],
        email=userinfo['email'],
        name=userinfo['name'],
        email_verified=userinfo.get('email_verified') is True,
    )

    connection_details = ConnectionDetails(
        ip_address=request.headers.get("X-Real-IP"),
        user_agent=request.headers.get("User-Agent"),
    )
    session_id = await auth_service.create_session(
        user_id=account.user_id,
        connection_details=connection_details
    )

    redirect = RedirectResponse(url=app_config.auth.oauth_redirect_url)
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        max_age=app_config.auth.cookie_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=(settings.env == "prod"),
    )
    return redirect


@user_controller.post("/tokens/verify-email")
async def request_verification_email(
    user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    await auth_service.send_verification_email(user.id)
    return {"message": "Verification email sent"}


@user_controller.post("/tokens/forgot-password")
async def forgot_password(
    payload: ForgottenPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    await auth_service.send_password_reset_email(payload.email)
    return {"message": "Password reset email sent"}


@user_controller.post("/tokens/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    await auth_service.reset_password(payload.token, payload.new_password)
    return {"message": "Password reset"}


@user_controller.get("/tokens/verify")
async def verify_token(
    token: AuthTokenInput,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.verify_email(token)
    except AuthError:
        return RedirectResponse(
            url=f"{app_config.auth.frontend_base_url}/email-verified?error=invalid"
        )

    return RedirectResponse(
        url=f"{app_config.auth.frontend_base_url}/email-verified"
    )


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
    return UserResponse.from_user_row(user)


@user_controller.get("/me/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    request: Request,
    current_user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> DashboardResponse:
    return await auth_service.get_dashboard(user_id=current_user.id)


@user_controller.get("/me/notifications")
async def get_notifications(
    request: Request,
    current_user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> StreamingResponse:
    return StreamingResponse(
        auth_service.stream_notifications(current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@user_controller.get("/me/links/editor")
async def get_editor_links(
    request: Request,
    current_user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserNavigationResponse:
    return await auth_service.get_editor_links(current_user.id)


@user_controller.get("/me/links/chat")
async def get_chat_links(
    request: Request,
    current_user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> StoryNavigationResponse:
    return await auth_service.get_chat_links(current_user.id)


@user_controller.patch("/me/settings")
async def update_settings(
    request: Request,
    payload: SettingsPayload,
    current_user: UserRow = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    return await auth_service.update_settings(current_user.id, payload)
