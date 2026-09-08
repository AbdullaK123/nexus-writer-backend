from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.data.repositories.user import UserRepository


async def test_customer_id_is_not_discarded_when_loading_an_existing_user():
    now = datetime.now(timezone.utc)
    stored = dict(id="u1", username="writer", email="writer@example.com", password_hash=None,
                  settings={}, profile_img=None, email_verified=True, created_at=now,
                  updated_at=now, stripe_customer_id="cus_existing")
    executor = AsyncMock()

    async def select(sql, *args):
        columns = sql.split("SELECT", 1)[1].split("FROM", 1)[0].strip().split(",")
        return {name.strip(): stored[name.strip()] for name in columns}

    executor.fetchrow.side_effect = select
    user = await UserRepository(executor).get_by_email("writer@example.com")
    assert user.stripe_customer_id == "cus_existing", "dropping the stored customer ID creates duplicate payment identities on subsequent checkouts"


@pytest.mark.parametrize("found", [False, True])
async def test_customer_lookup_reads_a_row_instead_of_a_command_status(found):
    now = datetime.now(timezone.utc)
    executor = AsyncMock()
    executor.execute.return_value = "SELECT 1" if found else "SELECT 0"
    executor.fetchrow.return_value = dict(id="u1", username="writer", email="writer@example.com",
        password_hash=None, settings={}, profile_img=None, email_verified=True,
        created_at=now, updated_at=now, stripe_customer_id="cus_existing") if found else None
    user = await UserRepository(executor).get_by_stripe_customer_id("cus_existing")
    assert (user is not None) == found, "payment webhooks must resolve their owner without trying to deserialize an SQL command status"
