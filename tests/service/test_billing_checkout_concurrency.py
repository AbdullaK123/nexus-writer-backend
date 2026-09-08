import asyncio
from types import SimpleNamespace

import pytest
import stripe

from src.service.exceptions import ConflictError, InternalError
from tests.service.mocks.billing import billing_harness, StripePage, subscription


async def test_concurrent_checkouts_share_one_customer_and_open_session(monkeypatch):
    h = billing_harness(monkeypatch, customer_id=None)
    entered, release = asyncio.Event(), asyncio.Event()
    sessions = []

    async def create(**kwargs):
        entered.set()
        await release.wait()
        session = SimpleNamespace(id="cs_1", mode="subscription", status="open", url="https://checkout.test/1")
        sessions.append(session)
        return session

    h.client.v1.checkout.sessions.create_async.side_effect = create
    h.client.v1.checkout.sessions.list_async.side_effect = lambda **kw: StripePage(sessions[:])
    first = asyncio.create_task(h.service.create_checkout_session("user-1"))
    await asyncio.wait_for(entered.wait(), 2)
    second = asyncio.create_task(h.service.create_checkout_session("user-1"))
    try:
        await asyncio.wait_for(h.pool.waiting.wait(), 2)
    finally:
        release.set()
    results = await asyncio.wait_for(asyncio.gather(first, second), 2)
    assert results == ["https://checkout.test/1"] * 2, "two browser tabs must return the same checkout rather than offer two payable subscriptions"
    assert h.client.v1.customers.create_async.await_count == 1, "concurrent requests must not split one user across different Stripe customers"
    assert h.client.v1.checkout.sessions.create_async.await_count == 1, "serializing only customer creation still permits duplicate charges from separate checkouts"


@pytest.mark.parametrize("status", ["active", "incomplete", "past_due", "unpaid", "paused"])
async def test_checkout_cannot_duplicate_a_subscription_before_its_webhook_arrives(monkeypatch, status):
    h = billing_harness(monkeypatch)
    h.client.v1.subscriptions.list_async.return_value = StripePage([subscription(status=status)])
    with pytest.raises(ConflictError):
        await h.service.create_checkout_session("user-1")
    assert h.client.v1.checkout.sessions.create_async.await_count == 0, "a lagging local subscription row must not permit a second chargeable subscription"


async def test_checkout_retry_uses_the_same_idempotency_key_after_lost_response(monkeypatch):
    h = billing_harness(monkeypatch)
    create = h.client.v1.checkout.sessions.create_async
    create.side_effect = [stripe.APIConnectionError("lost response"), SimpleNamespace(url="https://checkout.test/1")]
    with pytest.raises(InternalError):
        await h.service.create_checkout_session("user-1")
    await h.service.create_checkout_session("user-1")
    keys = [call.kwargs["options"]["idempotency_key"] for call in create.await_args_list]
    assert keys[0] == keys[1], "retrying after an ambiguous network failure must not create a second Stripe checkout"


async def test_expired_checkout_does_not_reuse_its_old_creation_key(monkeypatch):
    h = billing_harness(monkeypatch)
    h.client.v1.checkout.sessions.list_async.return_value = StripePage([
        SimpleNamespace(id="cs_expired", status="expired", mode="subscription"),
    ])
    await h.service.create_checkout_session("user-1")
    key = h.client.v1.checkout.sessions.create_async.await_args.kwargs["options"]["idempotency_key"]
    assert key.endswith(":cs_expired"), "an expired attempt must allow a fresh payable checkout instead of replaying the expired session forever"


async def test_payment_finishing_during_checkout_lookup_cannot_open_another_checkout(monkeypatch):
    h = billing_harness(monkeypatch)

    async def sessions(**kwargs):
        # The browser completes payment while the checkout-list request is in flight.
        h.client.v1.subscriptions.list_async.return_value = StripePage([subscription()])
        return StripePage([SimpleNamespace(id="cs_paid", mode="subscription", status="complete")])

    h.client.v1.checkout.sessions.list_async.side_effect = sessions
    with pytest.raises(ConflictError):
        await h.service.create_checkout_session("user-1")
    assert h.client.v1.checkout.sessions.create_async.await_count == 0, "a subscription check made before checkout lookup can miss payment completion and allow a second charge"
