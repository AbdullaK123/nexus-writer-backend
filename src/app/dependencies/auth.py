from fastapi import Request, Cookie, Depends

from src.data.schemas import UserRow
from src.app.dependencies.services import get_auth_service
from src.service.auth import AuthService
from src.shared.utils.correlation import set_user_id


async def get_current_user(
    request: Request,
    session_id: str = Cookie(),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRow:
    user = await auth_service.validate_session(session_id)
    try:
        request.state.user_id = user.id
    except Exception:
        pass
    try:
        set_user_id(user.id)
    except Exception:
        pass
    return user
