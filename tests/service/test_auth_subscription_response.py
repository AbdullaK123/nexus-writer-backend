import pytest

from src.data.schemas.auth import ConnectionDetails, UserResponse


@pytest.mark.parametrize("status", [None, "canceled", "past_due"])
async def test_existing_session_reflects_subscription_changes_without_logging_in_again(
    auth_service, fake_user_repo, test_user, status,
):
    session_id = await auth_service.create_session(test_user.id, ConnectionDetails())
    fake_user_repo.subscription_statuses[test_user.id] = "active"
    previous = await auth_service.validate_session(session_id)
    fake_user_repo.subscription_statuses[test_user.id] = status

    current = await auth_service.validate_session(session_id)

    assert previous.subscription_status == "active", "the scenario must begin with paid access so stale status would remain visible"
    assert isinstance(current, UserResponse), "session validation must return the public response instead of exposing the database user record"
    assert current.subscription_status == status, "subscription changes must reach existing sessions without requiring a fresh login"
    assert not {"password_hash", "stripe_customer_id"} & current.model_dump().keys(), "session responses must not expose private account fields to controllers"
