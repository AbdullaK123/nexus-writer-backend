from fastapi import Request, Cookie
from dependency_injector.wiring import inject, Provide
from src.service.auth.service import AuthService
from src.data.models import User
from src.shared.utils.logging_context import set_user_id
from typing import Optional, Union


@inject
async def get_current_user(
    request: Request,
    session_id: Union[bytes, str] = Cookie(),
    auth_service: AuthService = Provide["auth_service"]
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
