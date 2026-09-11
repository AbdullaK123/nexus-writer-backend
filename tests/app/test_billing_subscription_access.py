import pytest

from src.app.dependencies.auth import require_active_subscription
from src.service.exceptions import ForbiddenError


@pytest.mark.parametrize("status", [None, "canceled", "incomplete", "incomplete_expired", "unpaid", "paused"])
async def test_non_entitled_subscription_cannot_pass_the_paid_access_boundary(app_user_response, status):
    user = app_user_response.model_copy(update={"subscription_status": status})
    with pytest.raises(ForbiddenError) as exc_info:
        await require_active_subscription(user)
    assert exc_info.value.status_code == 403, "non-entitled accounts must receive an access denial rather than enter paid routes"
