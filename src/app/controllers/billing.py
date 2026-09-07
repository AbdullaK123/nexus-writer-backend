from typing import cast
from loguru import logger
from fastapi import APIRouter, Depends, Request
from stripe import Invoice, Subscription, Webhook
import stripe
from stripe.checkout import Session
from src.infrastructure.config import settings as app_settings
from src.app.dependencies.auth import get_verified_user
from src.app.dependencies.services import get_billing_service
from src.data.schemas.auth import UserRow
from src.service.billing.service import BillingService
from src.service.exceptions import ForbiddenError
from src.app.dependencies.rate_limit import webhook_rate_limit


billing_controller = APIRouter(prefix="/billing")

@billing_controller.post("/checkout")
async def create_checkout(
    user: UserRow = Depends(get_verified_user),
    billing_service: BillingService = Depends(get_billing_service),
) -> dict[str, str]:
    url = await billing_service.create_checkout_session(user.id)
    return {"checkout_url": url}


@billing_controller.post("/webhook", dependencies=[webhook_rate_limit])
async def handle_webhook(
    request: Request,
    billing_service: BillingService = Depends(get_billing_service)
) -> dict[str, bool]:

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=app_settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        raise ForbiddenError("Invalid webhook signature")

    event_type = event.type

    try:
        match event_type:
            case "checkout.session.completed":
                await billing_service.handle_checkout_completed(
                    cast(Session, event.data.object)
                )
            case "customer.subscription.updated":
                await billing_service.handle_subscription_updated(
                    cast(Subscription, event.data.object)
                )
            case "customer.subscription.deleted":
                await billing_service.handle_subscription_deleted(
                    cast(Subscription, event.data.object)
                )
            case "invoice.payment_failed":
                await billing_service.handle_payment_failed(
                    cast(Invoice, event.data.object)
                )
            case "invoice.payment_succeeded":
                await billing_service.handle_payment_succeeded(
                    cast(Invoice, event.data.object)
                )
            case _:
                logger.debug("stripe.webhook.unhandled_event", event_type=event_type)
    except Exception:
        logger.exception("stripe.webhook.handler_failed", event_type=event_type)

    return {"received": True}