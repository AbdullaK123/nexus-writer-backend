from fastapi import Request, Cookie, Depends
from src.data.models import User
from src.shared.utils.logging_context import set_user_id
from src.service.auth.service import AuthService
from src.app.dependencies.services import get_auth_service
from typing import Optional


async def get_current_user(
    request: Request,
    session_id: str = Cookie(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    user = await auth_service.validate_session(session_id)
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
