import pytest

from src.data.schemas.auth import RegistrationData
from src.service.exceptions import InternalError


class FakeResendError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def _install_failing_resend(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_send(payload: dict):
        raise FakeResendError("provider-secret-diagnostic")

    monkeypatch.setattr("src.service.auth.service.ResendError", FakeResendError)
    monkeypatch.setattr("src.service.auth.service.resend.Emails.send_async", fail_send)


async def test_registration_remains_successful_after_canonical_user_commit_if_email_delivery_fails(
    auth_service,
    fake_user_repo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _install_failing_resend(monkeypatch)

    response = await auth_service.register_user(
        RegistrationData(
            username="mail-failure-user",
            email="mail-failure@example.com",
            password="Strong1!Password",
        )
    )

    stored = await fake_user_repo.get_by_email("mail-failure@example.com")
    assert stored is not None
    assert response.id == stored.id, (
        "an external mail outage must not turn an already-committed registration into an apparent failure"
    )


async def test_forgot_password_is_indistinguishable_for_missing_unverified_and_mail_failure(
    auth_service,
    fake_user_repo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _install_failing_resend(monkeypatch)

    unverified = await fake_user_repo.create(
        username="unverified",
        email="unverified@example.com",
        password_hash="hash",
        profile_img=None,
        verified=False,
    )
    verified = await fake_user_repo.create(
        username="verified",
        email="verified@example.com",
        password_hash="hash",
        profile_img=None,
        verified=True,
    )

    assert await auth_service.send_password_reset_email("missing@example.com") is None
    assert await auth_service.send_password_reset_email(unverified.email) is None
    assert await auth_service.send_password_reset_email(verified.email) is None


async def test_verification_resend_hides_provider_diagnostics(
    auth_service,
    fake_user_repo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _install_failing_resend(monkeypatch)
    user = await fake_user_repo.create(
        username="verify-provider-failure",
        email="verify-provider-failure@example.com",
        password_hash="hash",
        profile_img=None,
        verified=False,
    )

    with pytest.raises(InternalError) as exc_info:
        await auth_service.send_verification_email(user.id)

    assert "provider-secret-diagnostic" not in str(exc_info.value)


async def test_verified_user_resend_is_a_noop_without_new_token_or_email(
    auth_service,
    fake_user_repo,
    fake_auth_token_repo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def count_send(payload: dict):
        nonlocal calls
        calls += 1
        return {"id": "email"}

    monkeypatch.setattr("src.service.auth.service.resend.Emails.send_async", count_send)
    user = await fake_user_repo.create(
        username="already-verified",
        email="already-verified@example.com",
        password_hash="hash",
        profile_img=None,
        verified=True,
    )

    await auth_service.send_verification_email(user.id)

    assert calls == 0
    assert not any(
        row.user_id == user.id and row.purpose == "email_verification"
        for row in fake_auth_token_repo._tokens.values()
    )
