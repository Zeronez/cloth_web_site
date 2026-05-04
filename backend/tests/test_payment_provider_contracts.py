from decimal import Decimal
import hashlib
import hmac
import json
from urllib.parse import parse_qs, urlparse

import pytest

from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod
from payments.serializers import PaymentWebhookSerializer


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "US",
        "shipping_city": "New York",
        "shipping_postal_code": "10001",
        "shipping_line1": "11 Test Avenue",
        "shipping_line2": "Apt 5",
    }
    payload.update(overrides)
    return payload


def sign_payload(payload, secret):
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return raw, signature


def create_session_order(user, *, total_amount="125.00"):
    return Order.objects.create(
        user=user,
        total_amount=Decimal(total_amount),
        **shipping_payload(),
    )


def create_strict_provider_payment(user, *, provider_code="yookassa"):
    method = PaymentMethod.objects.create(
        code=f"{provider_code}-card",
        name=f"{provider_code} card",
        provider_code=provider_code,
        session_mode="redirect",
    )
    order = create_session_order(user)
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
        message="Seeded for provider contract tests.",
        payload={"order_id": order.id},
    )
    return order, payment


def test_placeholder_session_contract_returns_stable_provider_envelope(
    authenticated_client, user
):
    order = create_session_order(user)
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Local card",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )

    first_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": order.id,
            "payment_method_code": method.code,
            "idempotency_key": "provider-contract-1",
        },
        format="json",
    )
    replay_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": order.id,
            "payment_method_code": method.code,
            "idempotency_key": "provider-contract-1",
        },
        format="json",
    )

    assert first_response.status_code == 201
    assert replay_response.status_code == 200

    for response in (first_response, replay_response):
        assert response.data["provider"] == "placeholder"
        assert response.data["confirmation_url"] is None
        assert response.data["message"] == (
            "Платежная сессия создана локально. Внешний провайдер не подключен."
        )

    assert replay_response.data["message"] == first_response.data["message"]
    assert replay_response.data["payment"]["id"] == first_response.data["payment"]["id"]


def test_strict_webhook_serializer_normalizes_path_provider_and_payload():
    serializer = PaymentWebhookSerializer(
        data={
            "event_id": "strict-event-serializer-1",
            "provider": "yookassa",
            "status": Payment.Status.AUTHORIZED,
            "order_id": 101,
        },
        context={"provider_code": "yookassa"},
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["provider"] == "yookassa"
    assert serializer.validated_data["payload"] == {}


def test_yookassa_session_contract_returns_redirect_envelope(
    authenticated_client, user, settings
):
    settings.PAYMENT_PROVIDER_CONFIRMATION_URLS = {
        "yookassa": "https://pay.example.test/session"
    }
    settings.PAYMENT_PROVIDER_RETURN_BASE_URL = (
        "https://animeattire.example/checkout/return"
    )
    order = create_session_order(user)
    method = PaymentMethod.objects.create(
        code="yookassa-card",
        name="YooKassa card",
        provider_code="yookassa",
        session_mode="redirect",
    )

    response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": order.id,
            "payment_method_code": method.code,
            "idempotency_key": "strict-provider-session-1",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["provider"] == "yookassa"
    assert response.data["confirmation_url"].startswith(
        "https://pay.example.test/session/yookassa-sandbox-"
    )
    confirmation_query = parse_qs(urlparse(response.data["confirmation_url"]).query)
    assert "return_url" in confirmation_query
    return_url = confirmation_query["return_url"][0]
    parsed_return = urlparse(return_url)
    return_query = parse_qs(parsed_return.query)
    assert parsed_return.scheme == "https"
    assert parsed_return.netloc == "animeattire.example"
    assert parsed_return.path == "/checkout/return"
    assert return_query["provider"] == ["yookassa"]
    assert return_query["order_id"] == [str(order.id)]
    assert return_query["payment_id"] == [str(response.data["payment"]["id"])]
    assert response.data["message"] == (
        "Платежная сессия YooKassa подготовлена в sandbox-режиме."
    )
    assert response.data["payment"]["provider_code"] == "yookassa"
    assert response.data["payment"]["external_payment_id"].startswith(
        "yookassa-sandbox-"
    )


def test_strict_provider_webhook_accepts_normalized_payload_and_processes_generically(
    api_client, user, settings
):
    settings.PAYMENT_WEBHOOK_BYPASS_PROVIDERS = ["manual", "placeholder", "local"]
    settings.PAYMENT_WEBHOOK_SECRETS = {"yookassa": "super-secret"}
    settings.PAYMENT_WEBHOOK_SIGNATURE_HEADERS = {"yookassa": "X-Payment-Signature"}
    order, payment = create_strict_provider_payment(user, provider_code="yookassa")
    payload = {
        "event_id": "strict-event-1",
        "provider": "yookassa",
        "status": "succeeded",
        "order_id": order.id,
        "payment_id": payment.id,
        "payload": {"source": "strict-provider"},
    }
    _, signature = sign_payload(payload, "super-secret")

    response = api_client.post(
        "/api/payments/webhooks/yookassa/",
        payload,
        format="json",
        HTTP_X_PAYMENT_SIGNATURE=f"sha256={signature}",
    )

    assert response.status_code == 200
    assert response.data["code"] == "processed"
    assert response.data["processed"] is True
    assert response.data["replayed"] is False

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED
    assert order.status == Order.Status.PAID

    webhook_event = PaymentEvent.objects.get(
        payment=payment, external_event_id="strict-event-1"
    )
    assert webhook_event.payload == {"source": "strict-provider"}
