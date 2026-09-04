from src.data.schemas.auth import RegistrationData, UserResponse


class StubAuthService:
    def __init__(self, user_response: UserResponse) -> None:
        self.user_response = user_response
        self.registration_calls: list[RegistrationData] = []
        self.verification_email_calls: list[str] = []
        self.forgot_password_calls: list[str] = []
        self.reset_password_calls: list[tuple[str, str]] = []
        self.verify_email_calls: list[str] = []
        self.verify_error: Exception | None = None

    async def register_user(self, registration_data: RegistrationData) -> UserResponse:
        self.registration_calls.append(registration_data)
        return self.user_response

    async def send_verification_email(self, user_id: str) -> None:
        self.verification_email_calls.append(user_id)

    async def send_password_reset_email(self, email: str) -> None:
        self.forgot_password_calls.append(str(email))

    async def reset_password(self, token: str, new_password: str) -> None:
        self.reset_password_calls.append((token, new_password))

    async def verify_email(self, token: str) -> None:
        self.verify_email_calls.append(token)
        if self.verify_error is not None:
            raise self.verify_error
