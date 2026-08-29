import pytest

from src.data.schemas.auth import AuthCredentials, UserResponse
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError


async def test_missing_and_wrong_password_paths_do_equivalent_hash_work(
    auth_service: AuthService,
    test_user: UserResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verify_calls: list[tuple[str, str]] = []

    def fake_verify(password: str, password_hash: str) -> bool:
        verify_calls.append((password, password_hash))
        return False

    monkeypatch.setattr("src.service.auth.service.verify_password", fake_verify)

    with pytest.raises(AuthError, match="Incorrect email or password"):
        await auth_service.authenticate_user(
            AuthCredentials(
                email="definitely-missing@example.com",
                password="WrongPassword!123",
            )
        )
    missing_account_hash_calls = len(verify_calls)

    verify_calls.clear()

    with pytest.raises(AuthError, match="Incorrect email or password"):
        await auth_service.authenticate_user(
            AuthCredentials(
                email="testuser@email.com",
                password="WrongPassword!123",
            )
        )
    existing_account_hash_calls = len(verify_calls)

    assert missing_account_hash_calls == existing_account_hash_calls == 1, (
        "nonexistent accounts must perform comparable password-hash work to wrong-password "
        "accounts; otherwise response timing becomes an account-enumeration oracle"
    )
