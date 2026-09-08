import stripe
from contextlib import asynccontextmanager
from stripe import StripeClient
from stripe.checkout import Session as CheckoutSession
from stripe import Subscription as StripeSubscription
from stripe import Invoice as StripeInvoice
from src.data.repositories.billing import SubscriptionRepository
from src.data.repositories.user import UserRepository
from src.infrastructure.config import settings as app_settings, config as app_config
from src.service.exceptions import ConflictError, InternalError, NotFoundError

from src.service.utils.decorators import handle_service_errors

class BillingService:

    def __init__(
        self,
        user_repo: UserRepository,
        subscription_repo: SubscriptionRepository
    ):
        self._user_repo = user_repo
        self._subscription_repo = subscription_repo
        self._client = StripeClient(api_key=app_settings.stripe_secret_key)

    @asynccontextmanager
    async def _locked(self, user_id: str):
        # The same database lock is shared by checkout and webhook reconciliation,
        # including requests handled by different API processes.
        async with self._user_repo.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                    f"billing:{user_id}",
                )
                yield conn

    @handle_service_errors
    async def create_checkout_session(self, user_id: str) -> str:
        try:
            async with self._locked(user_id) as conn:
                user = await self._user_repo.get_by_id(user_id, executor=conn)
                if user is None:
                    raise NotFoundError("User not found")

                if user.stripe_customer_id is None:
                    customer = await self._client.v1.customers.create_async(
                        # Stable parameters allow retries even if the user edits their email.
                        params={"metadata": {"user_id": user.id}},
                        options={"idempotency_key": f"billing-customer:{user.id}"},
                    )
                    await self._user_repo.set_stripe_customer_id(user.id, customer.id, executor=conn)
                    user = await self._user_repo.get_by_id(user.id, executor=conn)
                if user is None or user.stripe_customer_id is None:
                    raise InternalError("Could not associate payment customer")
            # Commit the customer mapping before checkout can fail. Otherwise a
            # checkout timeout would roll back an already-created Stripe customer.
            async with self._locked(user_id) as conn:
                user = await self._user_repo.get_by_id(user_id, executor=conn)
                if user is None or user.stripe_customer_id is None:
                    raise NotFoundError("Payment customer not found")
                customer_id = user.stripe_customer_id

                sessions = await self._client.v1.checkout.sessions.list_async(
                    params={"customer": customer_id, "limit": 100},
                )
                latest = pending = None
                async for session in sessions.auto_paging_iter():
                    if session.mode != "subscription":
                        continue
                    if latest is None:
                        latest = session
                    if session.status == "open" and pending is None:
                        pending = session

                # Read subscriptions AFTER sessions: a browser can finish payment
                # while these API requests run, independently of our database lock.
                subscriptions = await self._client.v1.subscriptions.list_async(
                    params={"customer": customer_id, "status": "all", "limit": 100},
                )
                async for subscription in subscriptions.auto_paging_iter():
                    if subscription.status not in ("canceled", "incomplete_expired"):
                        raise ConflictError("You already have a subscription. Manage it before starting another.")
                if pending is not None:
                    if pending.url is None:
                        raise InternalError("Checkout URL unavailable")
                    return pending.url

                previous = latest.id if latest is not None else "initial"
                session = await self._client.v1.checkout.sessions.create_async(
                    params={
                        "customer": customer_id,
                        "mode": "subscription",
                        "line_items": [{"price": app_settings.stripe_price_id, "quantity": 1}],
                        "success_url": f"{app_config.auth.frontend_base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                        "cancel_url": f"{app_config.auth.frontend_base_url}/billing/cancel",
                    },
                    options={"idempotency_key": f"billing-checkout:{user.id}:{previous}"},
                )
                if session.url is None:
                    raise InternalError("Failed to create checkout session")
                return session.url
        except stripe.StripeError as exc:
            raise InternalError("Payment service unavailable; please retry") from exc

    async def _reconcile_customer(self, customer) -> None:
        if customer is None:
            return
        customer_id = customer if isinstance(customer, str) else customer.id
        user = await self._user_repo.get_by_stripe_customer_id(customer_id)
        # Events for deleted users or customers outside this app have no local owner.
        if user is None:
            return

        try:
            async with self._locked(user.id) as conn:
                user = await self._user_repo.get_by_id(user.id, executor=conn)
                if user is None or user.stripe_customer_id != customer_id:
                    return
                # Fetch AFTER taking the lock: an older handler cannot overwrite a
                # newer handler's result with a snapshot fetched while it waited.
                subscriptions = await self._client.v1.subscriptions.list_async(
                    params={"customer": customer_id, "status": "all", "limit": 100},
                )
                latest = current = None
                async for subscription in subscriptions.auto_paging_iter():
                    if latest is None:
                        latest = subscription
                    if subscription.status not in ("canceled", "incomplete_expired"):
                        if current is not None:
                            raise InternalError("Multiple current subscriptions require reconciliation")
                        current = subscription
                subscription = current or latest
                if subscription is None:
                    await self._subscription_repo.delete_by_user_id(user_id=user.id, executor=conn)
                    return
                item = subscription.items.data[0]
                await self._subscription_repo.upsert(
                    user_id=user.id,
                    stripe_subscription_id=subscription.id,
                    status=subscription.status,
                    price_id=item.price.id,
                    current_period_start=item.current_period_start,
                    current_period_end=item.current_period_end,
                    cancel_at_period_end=subscription.cancel_at_period_end,
                    executor=conn,
                )
        except stripe.StripeError as exc:
            raise InternalError("Payment service unavailable; please retry") from exc

    # Events are wake-ups, not ordered state updates. The same current-state
    # reconciliation handles duplicates, late events, and replacement subscriptions.
    @handle_service_errors
    async def handle_checkout_completed(self, session: CheckoutSession) -> None:
        if session.mode == "subscription":
            await self._reconcile_customer(session.customer)

    @handle_service_errors
    async def handle_subscription_updated(self, subscription: StripeSubscription) -> None:
        await self._reconcile_customer(subscription.customer)

    @handle_service_errors
    async def handle_subscription_deleted(self, subscription: StripeSubscription) -> None:
        await self._reconcile_customer(subscription.customer)

    @handle_service_errors
    async def handle_payment_failed(self, invoice: StripeInvoice) -> None:
        await self._reconcile_customer(invoice.customer)

    @handle_service_errors
    async def handle_payment_succeeded(self, invoice: StripeInvoice) -> None:
        await self._reconcile_customer(invoice.customer)
