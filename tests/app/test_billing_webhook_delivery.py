import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.app.controllers.billing import billing_controller
from src.app.dependencies.redis import get_redis
from src.app.dependencies.services import get_auth_service, get_billing_service
from src.infrastructure.config import settings
from src.service.exceptions import ServiceError


@pytest.fixture
async def webhook_client():
    app = FastAPI()
    app.include_router(billing_controller)
    service = AsyncMock()
    redis = AsyncMock()
    redis.eval.return_value = 1
    app.dependency_overrides[get_billing_service] = lambda: service
    app.dependency_overrides[get_auth_service] = lambda: None
    app.dependency_overrides[get_redis] = lambda: redis

    @app.exception_handler(ServiceError)
    async def service_error(request, error):
        return JSONResponse(status_code=error.status_code, content={"detail": error.message})

    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        yield client, service


def signed_event():
    payload = json.dumps({"id": "evt_test", "object": "event", "type": "checkout.session.completed",
                          "data": {"object": {"id": "cs_test", "object": "checkout.session"}}}).encode()
    timestamp = int(time.time())
    digest = hmac.new(settings.stripe_webhook_secret.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256).hexdigest()
    return payload, {"Stripe-Signature": f"t={timestamp},v1={digest}"}


async def test_signed_webhook_without_browser_cookie_reaches_billing(webhook_client):
    client, service = webhook_client
    payload, headers = signed_event()
    response = await client.post("/billing/webhook", content=payload, headers=headers)
    assert response.status_code == 200, "Stripe has no browser session; requiring one prevents all paid entitlement updates"
    assert service.handle_checkout_completed.await_count == 1, "a signed payment event must reach billing without user authentication"


async def test_failed_handler_is_not_acknowledged_as_delivered(webhook_client):
    client, service = webhook_client
    service.handle_checkout_completed.side_effect = RuntimeError("database unavailable")
    payload, headers = signed_event()
    response = await client.post("/billing/webhook", content=payload, headers=headers)
    assert response.status_code == 500, "acknowledging failed processing loses Stripe retries and leaves paid accounts without access"
    assert "database unavailable" not in response.text, "webhook errors must not expose internal infrastructure details"


@pytest.mark.parametrize("headers", [{}, {"Stripe-Signature": "invalid"}])
async def test_unsigned_webhooks_cannot_change_entitlements(webhook_client, headers):
    client, service = webhook_client
    response = await client.post("/billing/webhook", content=b"{}", headers=headers)
    assert response.status_code == 403, "missing or invalid signatures must be rejected without requiring a browser session"
    assert service.handle_checkout_completed.await_count == 0, "unverified callers must not trigger subscription mutations"
