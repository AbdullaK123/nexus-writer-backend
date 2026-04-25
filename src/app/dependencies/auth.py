from fastapi import Request, Cookie
from src.data.models import User
from src.shared.utils.correlation import set_user_id
from src.service.auth.service import validate_session
from typing import Optional


async def get_current_user(
    request: Request,
    session_id: str = Cookie(),
) -> Optional[User]:
    user = await validate_session(session_id)
    if user is not None:
        try:
            request.state.user_id = user.id
        except Exception:
            pass
        try:
            set_user_id(user.id)
        except Exception:
            pass
    return user
