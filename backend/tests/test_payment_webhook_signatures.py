import hashlib
import hmac
import json
from decimal import Decimal

import pytest

from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Test street 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


def create_signed_payment(user, provider_code="yookassa"):
    method = PaymentMethod.objects.create(
        code=f"{provider_code}-card",
        name=f"{provider_code} card",
        provider_code=provider_code,
        session_mode=PaymentMethod.SessionMode.NONE,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=provider_code,
        status=Payment.Status.SESSION_CREATED,
        amount=order.total_amount,
        currency="RUB",
    )
    PaymentEvent.objects.create(
        payment=payment,
        event_type="seeded",
        previous_status="pending",
        new_status=payment.status,
        message="Seeded for webhook signature tests.",
        payload={"order_id": order.id},
    )
    return order, payment


def sign_payload(payload, secret):
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return raw, signature


def test_placeholder_provider_bypasses_signature_check(api_client, user):
    order, payment = create_signed_payment(user, provider_code="placeholder")

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "placeholder-event-1",
            "status": "succeeded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED


def test_webhook_accepts_valid_hmac_signature(api_client, user, settings):
    settings.PAYMENT_WEBHOOK_BYPASS_PROVIDERS = ["manual", "placeholder", "local"]
    settings.PAYMENT_WEBHOOK_SECRETS = {"yookassa": "super-secret"}
    settings.PAYMENT_WEBHOOK_SIGNATURE_HEADERS = {"yookassa": "X-Payment-Signature"}
    order, payment = create_signed_payment(user, provider_code="yookassa")
    payload = {
        "event_id": "signed-event-1",
        "status": "succeeded",
        "order_id": order.id,
        "payment_id": payment.id,
    }
    _, signature = sign_payload(payload, "super-secret")

    response = api_client.post(
        "/api/payments/webhooks/yookassa/",
        payload,
        format="json",
        HTTP_X_PAYMENT_SIGNATURE=f"sha256={signature}",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED


def test_webhook_rejects_missing_signature_for_strict_provider(
    api_client, user, settings
):
    settings.PAYMENT_WEBHOOK_BYPASS_PROVIDERS = ["manual", "placeholder", "local"]
    settings.PAYMENT_WEBHOOK_SECRETS = {"yookassa": "super-secret"}
    settings.PAYMENT_WEBHOOK_SIGNATURE_HEADERS = {"yookassa": "X-Payment-Signature"}
    order, payment = create_signed_payment(user, provider_code="yookassa")

    response = api_client.post(
        "/api/payments/webhooks/yookassa/",
        {
            "event_id": "signed-event-2",
            "status": "succeeded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 403
    assert response.data["webhook"]["code"] == "signature_missing"


def test_webhook_rejects_invalid_signature_for_strict_provider(
    api_client, user, settings
):
    settings.PAYMENT_WEBHOOK_BYPASS_PROVIDERS = ["manual", "placeholder", "local"]
    settings.PAYMENT_WEBHOOK_SECRETS = {"yookassa": "super-secret"}
    settings.PAYMENT_WEBHOOK_SIGNATURE_HEADERS = {"yookassa": "X-Payment-Signature"}
    order, payment = create_signed_payment(user, provider_code="yookassa")

    response = api_client.post(
        "/api/payments/webhooks/yookassa/",
        {
            "event_id": "signed-event-3",
            "status": "succeeded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
        HTTP_X_PAYMENT_SIGNATURE="sha256=deadbeef",
    )

    assert response.status_code == 403
    assert response.data["webhook"]["code"] == "signature_invalid"
