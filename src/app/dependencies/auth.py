from fastapi import Request, Cookie, Depends

from src.data.schemas import UserRow
from src.app.dependencies.services import get_auth_service
from src.service.auth import AuthService
from src.service.exceptions import AuthError, EmailVerificationRequiredError, ForbiddenError
from src.shared.utils.correlation import set_user_id


async def get_current_user(
    request: Request,
    session_id: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRow:
    
    if session_id is None:
        raise AuthError()

    try:
        user = await auth_service.validate_session(session_id)
    except ForbiddenError as exc:
        # A session that is missing, expired, or otherwise no longer valid means
        # the request is unauthenticated. HTTP 403 is reserved for a valid
        # identity that lacks permission (for example, unverified email).
        raise AuthError(exc.message) from exc

    try:
        request.state.user_id = user.id
    except Exception:
        pass

    try:
        set_user_id(user.id)
    except Exception:
        pass

    return user


async def get_verified_user(
    user: UserRow = Depends(get_current_user),
) -> UserRow:
    if not user.email_verified:
        raise EmailVerificationRequiredError()

    return user
