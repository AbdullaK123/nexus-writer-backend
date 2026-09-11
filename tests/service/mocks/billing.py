import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import stripe

from src.data.schemas.auth import UserRow
from src.data.repositories.user import UserRepository
from src.data.repositories.billing import SubscriptionRepository
from src.service.billing.service import BillingService


class BillingPool:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.waiting = asyncio.Event()

    @asynccontextmanager
    async def acquire(self):
        pool = self

        class Connection:
            held = False

            @asynccontextmanager
            async def transaction(self):
                try:
                    yield self
                finally:
                    if self.held:
                        pool.lock.release()

            async def execute(self, sql, *args):
                if pool.lock.locked():
                    pool.waiting.set()
                await pool.lock.acquire()
                self.held = True

        yield Connection()


class StripePage:
    def __init__(self, data):
        self.data = data

    async def auto_paging_iter(self):
        for item in self.data:
            yield item


def subscription(id="sub_1", status="active", created=1, customer="cus_1"):
    return stripe.Subscription.construct_from({
        "id": id, "object": "subscription", "customer": customer, "status": status,
        "created": created, "cancel_at_period_end": False,
        "items": {"object": "list", "data": [{"object": "subscription_item", "id": "si_1",
            "current_period_start": 100, "current_period_end": 200, "price": {"id": "price_fake"}}]},
    }, "sk_test_fake")


def billing_harness(monkeypatch, customer_id="cus_1"):
    pool = BillingPool()
    users = Mock(spec=UserRepository)
    users.pool = pool
    now = datetime.now(timezone.utc)
    state = {"user": UserRow(id="user-1", username="writer", email="writer@example.com",
        password_hash=None, profile_img=None, settings={}, email_verified=True,
        created_at=now, updated_at=now, stripe_customer_id=customer_id)}
    async def get_user(user_id, executor=None):
        user = state["user"]
        return (user, None) if user is not None else None

    users.get_by_id = AsyncMock(side_effect=get_user)
    users.get_by_stripe_customer_id = AsyncMock(side_effect=lambda *a, **kw: state["user"])

    async def set_customer(user_id, stripe_customer_id, executor=None):
        if state["user"].stripe_customer_id is None:
            state["user"] = state["user"].model_copy(update={"stripe_customer_id": stripe_customer_id})

    users.set_stripe_customer_id = AsyncMock(side_effect=set_customer)
    repo = Mock(spec=SubscriptionRepository)
    client = SimpleNamespace(v1=SimpleNamespace(
        customers=SimpleNamespace(create_async=AsyncMock(return_value=SimpleNamespace(id="cus_1"))),
        subscriptions=SimpleNamespace(list_async=AsyncMock(return_value=StripePage([]))),
        checkout=SimpleNamespace(sessions=SimpleNamespace(
            list_async=AsyncMock(return_value=StripePage([])),
            create_async=AsyncMock(return_value=SimpleNamespace(id="cs_1", url="https://checkout.test/1")),
        )),
    ))
    monkeypatch.setattr("src.service.billing.service.StripeClient", lambda **kw: client)
    return SimpleNamespace(service=BillingService(users, repo), users=users, repo=repo,
                           client=client, pool=pool, state=state)
