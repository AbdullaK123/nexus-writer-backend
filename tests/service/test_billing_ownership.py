from unittest.mock import AsyncMock

from tests.service.mocks.billing import billing_harness, subscription


async def test_unknown_customer_event_cannot_write_another_users_entitlement(monkeypatch):
    h = billing_harness(monkeypatch)
    h.users.get_by_stripe_customer_id.return_value = None
    h.users.get_by_stripe_customer_id.side_effect = None
    h.repo.upsert = AsyncMock()
    await h.service.handle_subscription_updated(subscription(customer="cus_unknown"))
    assert h.repo.upsert.await_count == 0, "a Stripe event without a local owner must never be attributed to an arbitrary account"
    assert h.client.v1.subscriptions.list_async.await_count == 0, "unowned Stripe customers must not trigger local reconciliation work"


async def test_changed_customer_mapping_is_rechecked_inside_the_lock(monkeypatch):
    h = billing_harness(monkeypatch)
    original = h.state["user"]
    h.users.get_by_stripe_customer_id.side_effect = lambda *a, **kw: original
    h.state["user"] = original.model_copy(update={"stripe_customer_id": "cus_replaced"})
    h.repo.upsert = AsyncMock()
    await h.service.handle_subscription_updated(subscription())
    assert h.repo.upsert.await_count == 0, "a customer mapping changed during dispatch must not overwrite the replacement account's entitlement"
