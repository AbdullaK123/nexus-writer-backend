import asyncio
from unittest.mock import AsyncMock

import pytest
import stripe

from src.service.exceptions import InternalError
from tests.service.mocks.billing import billing_harness, StripePage, subscription


@pytest.mark.parametrize("handler", ["handle_subscription_updated", "handle_subscription_deleted"])
async def test_old_event_cannot_overwrite_the_current_replacement_subscription(monkeypatch, handler):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    replacement = subscription(id="sub_new", created=2)
    h.client.v1.subscriptions.list_async.return_value = StripePage([replacement, subscription(status="canceled")])
    await getattr(h.service, handler)(subscription(id="sub_old", status="active"))
    stored = h.repo.upsert.await_args.kwargs
    assert stored["stripe_subscription_id"] == "sub_new", "a delayed event for an old subscription must not revoke or replace the user's new paid subscription"
    assert stored["status"] == "active", "current Stripe state must control entitlement even when the triggering event says otherwise"


async def test_old_active_event_cannot_reactivate_a_canceled_subscription(monkeypatch):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    h.client.v1.subscriptions.list_async.return_value = StripePage([subscription(status="canceled")])
    await h.service.handle_subscription_updated(subscription(status="active"))
    assert h.repo.upsert.await_args.kwargs["status"] == "canceled", "out-of-order webhook delivery must never restore access to a canceled subscription"


async def test_stripe_outage_does_not_overwrite_the_last_confirmed_entitlement(monkeypatch):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    h.repo.delete_by_user_id = AsyncMock()
    h.client.v1.subscriptions.list_async.side_effect = stripe.APIConnectionError("unavailable")
    with pytest.raises(InternalError):
        await h.service.handle_subscription_updated(subscription())
    assert h.repo.upsert.await_count == 0, "failed reconciliation must retain canonical state and let Stripe retry"
    assert h.repo.delete_by_user_id.await_count == 0, "a Stripe outage must not be mistaken for an empty subscription list"


async def test_concurrent_webhooks_fetch_current_state_only_after_acquiring_the_lock(monkeypatch):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def fetch(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await release.wait()
            return StripePage([subscription(status="active")])
        return StripePage([subscription(status="canceled")])

    h.client.v1.subscriptions.list_async.side_effect = fetch
    first = asyncio.create_task(h.service.handle_subscription_updated(subscription()))
    await asyncio.wait_for(entered.wait(), 2)
    second = asyncio.create_task(h.service.handle_subscription_deleted(subscription()))
    try:
        await asyncio.wait_for(h.pool.waiting.wait(), 2)
        assert calls == 1, "fetching before serialization allows a waiting handler to overwrite newer state with its stale snapshot"
    finally:
        release.set()
    await asyncio.wait_for(asyncio.gather(first, second), 2)
    assert h.repo.upsert.await_args.kwargs["status"] == "canceled", "the last serialized reconciliation must retain the latest cancellation"


async def test_subscription_update_before_checkout_webhook_still_creates_entitlement(monkeypatch):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    h.client.v1.subscriptions.list_async.return_value = StripePage([subscription()])
    await h.service.handle_subscription_updated(subscription())
    assert h.repo.upsert.await_count == 1, "Stripe does not guarantee checkout events arrive before subscription events"


async def test_multiple_live_subscriptions_are_not_silently_collapsed_into_one(monkeypatch):
    h = billing_harness(monkeypatch)
    h.repo.upsert = AsyncMock()
    h.client.v1.subscriptions.list_async.return_value = StripePage([subscription(id="sub_2"), subscription()])
    with pytest.raises(InternalError):
        await h.service.handle_subscription_updated(subscription())
    assert h.repo.upsert.await_count == 0, "duplicate paid subscriptions require attention rather than hiding one charge behind a single local row"
