import stripe
from stripe import StripeClient
from stripe.checkout import Session as CheckoutSession
from stripe import Subscription as StripeSubscription
from stripe import Invoice as StripeInvoice
from src.data.repositories.billing import SubscriptionRepository
from src.data.repositories.user import UserRepository
from src.infrastructure.config import settings as app_settings, config as app_config
from src.service.exceptions import ConflictError, InternalError, NotFoundError
from loguru import logger

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

    @handle_service_errors
    async def create_checkout_session(
        self,
        user_id: str
    ) -> str:

        user = await self._user_repo.get_by_id(user_id=user_id)

        if user is None:
            raise NotFoundError("User not found")

        existing = await self._subscription_repo.get_by_user_id(user_id=user.id)
        if existing and existing.status in ("active", "trialing", "past_due"):
            raise ConflictError("You already have an active subscription.")

        if user.stripe_customer_id is None:
            try:
                customer = await self._client.v1.customers.create_async(params={
                    "email": user.email
                })
                await self._user_repo.set_stripe_customer_id(user.id, customer.id)
                customer_id=customer.id
            except stripe.StripeError as e:
                logger.error("stripe.create_customer.failed", err=str(e))
                raise InternalError("Something went wrong with the payment service. Please try again.")
        else:
            customer_id = user.stripe_customer_id
            
        try:
            session = await self._client.v1.checkout.sessions.create_async(params={
                "customer": customer_id,
                "mode": "subscription",
                "line_items": [{
                    "price": app_settings.stripe_price_id,
                    "quantity": 1
                }],
                "success_url": f"{app_config.auth.frontend_base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{app_config.auth.frontend_base_url}/billing/cancel"
            })
            if session.url is None:
                raise InternalError("Failed to create checkout session")
            return session.url
        except stripe.StripeError as e:
            logger.error("stripe.create_checkout_session.failed", err=str(e))
            raise InternalError("Something went wrong with the payment service. Please try again.")
        
    @handle_service_errors
    async def handle_checkout_completed(self, session: CheckoutSession) -> None:

        sub_id = session.subscription

        if sub_id is None:
            logger.error("stripe.checkout.no_subscription", session_id=session.id)
            return

        if not isinstance(sub_id, str):
            sub_id = sub_id.id

        if session.customer is None:
            logger.error("stripe.checkout.no_customer", session_id=session.id)
            return

        customer_id = session.customer
        if not isinstance(customer_id, str):
            customer_id = customer_id.id

        try:
            sub = await self._client.v1.subscriptions.retrieve_async(sub_id)
        except stripe.StripeError as e:
            logger.error("stripe.retrieve_subscription.failed", err=str(e))
            raise InternalError("Payment service unavailable; please retry") from e

        user = await self._user_repo.get_by_stripe_customer_id(customer_id)

        if user is None:
            logger.error("stripe.checkout.no_user", customer_id=customer_id)
            return

        item = sub.items.data[0]
        period_start = item.current_period_start
        period_end = item.current_period_end
        price_id = item.price.id

        # Idempotent — if a subscription row already exists, update it
        existing = await self._subscription_repo.get_by_stripe_id(
            stripe_subscription_id=sub.id
        )

        if existing:
            await self._subscription_repo.update_status(
                stripe_subscription_id=sub.id,
                status=sub.status,
                current_period_start=period_start,
                current_period_end=period_end,
                cancel_at_period_end=sub.cancel_at_period_end,
            )
        else:
            await self._subscription_repo.create(
                user_id=user.id,
                stripe_subscription_id=sub.id,
                status=sub.status,
                price_id=price_id,
                current_period_start=period_start,
                current_period_end=period_end,
            )

        logger.info("stripe.checkout.completed", user_id=user.id, subscription_id=sub.id)

    @handle_service_errors
    async def handle_subscription_updated(self, subscription: StripeSubscription) -> None:

        existing = await self._subscription_repo.get_by_stripe_id(
            stripe_subscription_id=subscription.id
        )

        if existing is None:
            logger.warning("stripe.subscription.updated.not_found", subscription_id=subscription.id)
            return

        item = subscription.items.data[0]
        current_period_start = item.current_period_start
        current_period_end = item.current_period_end


        await self._subscription_repo.update_status(
            stripe_subscription_id=subscription.id,
            status=subscription.status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end
        )
        
        logger.info("stripe.subscription.updated", subscription_id=subscription.id, status=subscription.status)

    @handle_service_errors
    async def handle_subscription_deleted(self, subscription: StripeSubscription) -> None:
    
        existing = await self._subscription_repo.get_by_stripe_id(
            stripe_subscription_id=subscription.id
        )

        if existing is None:
            logger.warning("stripe.subscription.deleted.not_found", subscription_id=subscription.id)
            return

        item = subscription.items.data[0]
        current_period_start = item.current_period_start
        current_period_end = item.current_period_end


        await self._subscription_repo.update_status(
            stripe_subscription_id=subscription.id,
            status="canceled",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=False
        )
        
        logger.info("stripe.subscription.deleted", subscription_id=subscription.id, status=subscription.status)

    @handle_service_errors
    async def handle_payment_failed(self, invoice: StripeInvoice) -> None:

        customer_id = invoice.customer

        if customer_id is None:
            return

        if not isinstance(customer_id, str):
            customer_id = customer_id.id

        logger.warning(
            "stripe.payment_failed",
            customer_id=customer_id,
            attempt_count=invoice.attempt_count,
        )

    @handle_service_errors
    async def handle_payment_succeeded(self, invoice: StripeInvoice) -> None:

        customer_id = invoice.customer
        
        if customer_id is None:
            return

        if not isinstance(customer_id, str):
            customer_id = customer_id.id

        logger.info("stripe.payment_succeeded", customer_id=customer_id)