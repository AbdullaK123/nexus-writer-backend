from src.data.schemas.auth import RegistrationData, UserResponse


class StubAuthService:
    def __init__(self, user_response: UserResponse) -> None:
        self.user_response = user_response
        self.registration_calls: list[RegistrationData] = []

    async def register_user(self, registration_data: RegistrationData) -> UserResponse:
        self.registration_calls.append(registration_data)
        return self.user_response
