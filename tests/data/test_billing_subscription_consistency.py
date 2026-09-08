import asyncio

import pytest

from src.data.repositories.billing import SubscriptionRepository
from tests.data.factories import make_user


def snapshot(user_id, stripe_id="sub_original", status="active"):
    return dict(user_id=user_id, stripe_subscription_id=stripe_id, status=status,
                price_id="price_fake", current_period_start=100, current_period_end=200,
                cancel_at_period_end=False)


async def test_resubscription_replaces_canceled_row_without_unique_user_failure(clean_db):
    user = await make_user(clean_db)
    repo = SubscriptionRepository(clean_db)
    old = await repo.upsert(**snapshot(user.id, status="canceled"))
    new = await repo.upsert(**snapshot(user.id, "sub_replacement"))
    assert new.id == old.id, "resubscribing must update the one entitlement row rather than fail after the replacement has been paid for"
    assert new.stripe_subscription_id == "sub_replacement", "future billing events must resolve to the replacement subscription"
    count = await clean_db.fetchval('SELECT count(*) FROM "subscription" WHERE user_id=$1', user.id)
    assert count == 1, "one user must not acquire conflicting canonical entitlement rows"


async def test_concurrent_duplicate_snapshots_do_not_create_multiple_entitlements(clean_db):
    user = await make_user(clean_db)
    repo = SubscriptionRepository(clean_db)
    rows = await asyncio.gather(*(repo.upsert(**snapshot(user.id)) for _ in range(2)))
    assert rows[0].id == rows[1].id, "duplicate webhook deliveries must converge at the database constraint instead of raising unique violations"


async def test_rolled_back_reconciliation_preserves_previous_entitlement(clean_db):
    user = await make_user(clean_db)
    repo = SubscriptionRepository(clean_db)
    await repo.upsert(**snapshot(user.id))
    with pytest.raises(RuntimeError):
        async with clean_db.acquire() as conn:
            async with conn.transaction():
                await repo.upsert(**snapshot(user.id, status="canceled"), executor=conn)
                raise RuntimeError("injected failure before commit")
    saved = await repo.get_by_user_id(user_id=user.id)
    assert saved.status == "active", "an uncommitted reconciliation must not partially revoke the previously confirmed entitlement"


async def test_checkout_failure_does_not_rollback_an_already_created_customer(clean_db, monkeypatch):
    import stripe
    from src.data.repositories.user import UserRepository
    from src.service.billing.service import BillingService
    from src.service.exceptions import InternalError
    from tests.service.mocks.billing import billing_harness

    user = await make_user(clean_db)
    h = billing_harness(monkeypatch, customer_id=None)
    h.client.v1.checkout.sessions.create_async.side_effect = stripe.APIConnectionError("lost response")
    users = UserRepository(clean_db)
    service = BillingService(users, SubscriptionRepository(clean_db))
    with pytest.raises(InternalError):
        await service.create_checkout_session(user.id)
    saved = await users.get_by_id(user.id)
    assert saved.stripe_customer_id == "cus_1", "checkout failure must not orphan the Stripe customer whose creation already succeeded"
