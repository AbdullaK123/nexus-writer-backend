from httpx import AsyncClient
import pytest

from main import api
from src.app.dependencies import get_auth_service, get_current_user, get_verified_user
from src.data.schemas.auth import DashboardResponse, SettingsPayload, UserResponse, UserRow
from src.service.exceptions import EmailVerificationRequiredError
from tests.app.mocks import StubAuthService


@pytest.fixture
def unverified_user(app_user: UserRow) -> UserRow:
    return app_user.model_copy(update={"email_verified": False})


async def test_get_verified_user_returns_the_exact_verified_user(
    app_user: UserRow,
) -> None:
    result = await get_verified_user(app_user)

    assert result is app_user


async def test_get_verified_user_rejects_unverified_user_with_machine_readable_error(
    unverified_user: UserRow,
) -> None:
    with pytest.raises(EmailVerificationRequiredError) as exc_info:
        await get_verified_user(unverified_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "EMAIL_VERIFICATION_REQUIRED"
    assert exc_info.value.message == "Please verify your email to continue."


@pytest.mark.parametrize(
    "path",
    [
        "/api/auth/me/dashboard",
        "/api/stories",
        "/api/chapters/chapter-1",
        "/api/stories/story-1/chat/threads",
    ],
)
async def test_unverified_user_is_blocked_from_product_routes(
    app_client: AsyncClient,
    unverified_user: UserRow,
    path: str,
) -> None:
    async def current_user_override() -> UserRow:
        return unverified_user

    api.dependency_overrides[get_current_user] = current_user_override

    response = await app_client.get(path)

    assert response.status_code == 403, (
        f"{path} must reject authenticated but unverified users; otherwise email "
        "verification is only decorative authorization."
    )
    detail = response.json()["detail"]
    assert detail["code"] == "EMAIL_VERIFICATION_REQUIRED"
    assert detail["message"] == "Please verify your email to continue."


async def test_unverified_user_can_still_read_me_and_discover_verification_state(
    app_client: AsyncClient,
    unverified_user: UserRow,
) -> None:
    async def current_user_override() -> UserRow:
        return unverified_user

    api.dependency_overrides[get_current_user] = current_user_override

    response = await app_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["emailVerified"] is False, (
        "The frontend must be able to distinguish an authenticated unverified "
        "session from a fully authorized session."
    )


async def test_unverified_user_can_request_another_verification_email(
    app_client: AsyncClient,
    unverified_user: UserRow,
) -> None:
    service = StubAuthService(UserResponse.from_user_row(unverified_user))

    async def current_user_override() -> UserRow:
        return unverified_user

    async def auth_service_override() -> StubAuthService:
        return service

    api.dependency_overrides[get_current_user] = current_user_override
    api.dependency_overrides[get_auth_service] = auth_service_override

    response = await app_client.post("/api/auth/tokens/verify-email")

    assert response.status_code == 200, (
        "An unverified user must be able to escape the verification gate by "
        "requesting another verification email."
    )
    assert service.verification_email_calls == [unverified_user.id]


async def test_unverified_user_can_update_basic_settings(
    app_client: AsyncClient,
    unverified_user: UserRow,
) -> None:
    class SettingsAuthService(StubAuthService):
        def __init__(self, user_response: UserResponse) -> None:
            super().__init__(user_response)
            self.settings_calls: list[tuple[str, SettingsPayload]] = []

        async def update_settings(
            self,
            user_id: str,
            payload: SettingsPayload,
        ) -> UserResponse:
            self.settings_calls.append((user_id, payload))
            return self.user_response

    service = SettingsAuthService(UserResponse.from_user_row(unverified_user))

    async def current_user_override() -> UserRow:
        return unverified_user

    async def auth_service_override() -> SettingsAuthService:
        return service

    api.dependency_overrides[get_current_user] = current_user_override
    api.dependency_overrides[get_auth_service] = auth_service_override

    response = await app_client.patch(
        "/api/auth/me/settings",
        json={
            "kind": "appearance",
            "appearance": {"theme": "dark", "reducedMotion": False},
        },
    )

    assert response.status_code == 200, (
        "Verification should gate the application, not strand users outside "
        "basic account and accessibility settings."
    )
    assert len(service.settings_calls) == 1
    assert service.settings_calls[0][0] == unverified_user.id


async def test_same_session_becomes_authorized_immediately_after_verification(
    app_client: AsyncClient,
    unverified_user: UserRow,
) -> None:
    class MutableSessionAuthService:
        def __init__(self, user: UserRow) -> None:
            self.user = user

        async def validate_session(self, session_id: str) -> UserRow:
            assert session_id == "session-1"
            return self.user

        async def get_dashboard(self, user_id: str) -> DashboardResponse:
            assert user_id == self.user.id
            return DashboardResponse()

    service = MutableSessionAuthService(unverified_user)

    async def auth_service_override() -> MutableSessionAuthService:
        return service

    api.dependency_overrides[get_auth_service] = auth_service_override
    app_client.cookies.set("session_id", "session-1")

    before = await app_client.get("/api/auth/me/dashboard")
    assert before.status_code == 403
    assert before.json()["detail"]["code"] == "EMAIL_VERIFICATION_REQUIRED"

    service.user = service.user.model_copy(update={"email_verified": True})

    after = await app_client.get("/api/auth/me/dashboard")

    assert after.status_code == 200, (
        "Authorization must be derived from current canonical user state on "
        "every request; verification must not require issuing a new session."
    )
