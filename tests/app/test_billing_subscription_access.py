from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.app.dependencies.auth import require_active_subscription
from src.service.exceptions import ForbiddenError


@pytest.mark.parametrize("status", [None, "canceled", "incomplete", "incomplete_expired", "unpaid", "paused"])
async def test_non_entitled_subscription_cannot_pass_the_paid_access_boundary(status):
    repo = AsyncMock()
    repo.get_by_user_id.return_value = None if status is None else SimpleNamespace(status=status)
    with pytest.raises(ForbiddenError):
        await require_active_subscription(SimpleNamespace(id="user-1"), repo)
    assert repo.get_by_user_id.await_args.kwargs == {"user_id": "user-1"}, "paid access must be checked against the authenticated account, never a client-supplied owner"
