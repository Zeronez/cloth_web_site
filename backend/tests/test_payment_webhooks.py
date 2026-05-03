from decimal import Decimal

import pytest

from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod
from payments.services import create_payment_session


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


def create_payment_fixture(user):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    payment, _ = create_payment_session(
        user=user,
        order_id=order.id,
        payment_method_code=method.code,
        idempotency_key="payment-webhook-seed",
    )
    return order, payment


def test_payment_success_webhook_marks_payment_and_order_paid(api_client, user):
    order, payment = create_payment_fixture(user)

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-1",
            "status": "succeeded",
            "order_id": order.id,
            "payment_id": payment.id,
            "external_payment_id": "ext-9001",
            "payload": {"source": "test-provider"},
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["code"] == "processed"
    assert response.data["processed"] is True
    assert response.data["replayed"] is False
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED
    assert payment.external_payment_id == "ext-9001"
    assert order.status == Order.Status.PAID
    assert PaymentEvent.objects.filter(
        payment=payment,
        external_event_id="provider-event-1",
        new_status=Payment.Status.SUCCEEDED,
    ).exists()


def test_payment_webhook_replay_is_idempotent(api_client, user):
    order, payment = create_payment_fixture(user)

    first_response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-2",
            "status": "authorized",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )
    second_response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-2",
            "status": "authorized",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.data["code"] == "event_replayed"
    assert second_response.data["processed"] is False
    assert second_response.data["replayed"] is True
    assert (
        PaymentEvent.objects.filter(
            payment=payment,
            external_event_id="provider-event-2",
        ).count()
        == 1
    )


def test_payment_webhook_rejects_invalid_transition_after_success(api_client, user):
    order, payment = create_payment_fixture(user)
    payment.transition_to(
        Payment.Status.SUCCEEDED,
        event_type="manual_success",
        message="Manual success for test.",
        external_event_id="manual-success",
    )
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-3",
            "status": "failed",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 409
    assert response.data["webhook"]["code"] == "invalid_transition"
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED


def test_payment_webhook_requires_matching_provider(api_client, user):
    order, payment = create_payment_fixture(user)

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-4",
            "provider": "foreign-provider",
            "status": "authorized",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "provider" in response.data


def test_payment_failure_webhook_marks_payment_failed_without_changing_order_paid_state(
    api_client, user
):
    order, payment = create_payment_fixture(user)

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-5",
            "status": "failed",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.FAILED
    assert order.status == Order.Status.PENDING
    assert PaymentEvent.objects.filter(
        payment=payment,
        external_event_id="provider-event-5",
        new_status=Payment.Status.FAILED,
    ).exists()


def test_payment_refund_webhook_marks_payment_refunded_and_order_cancelled(
    api_client, user
):
    order, payment = create_payment_fixture(user)
    payment.transition_to(
        Payment.Status.SUCCEEDED,
        event_type="manual_success",
        message="Manual success for refund test.",
        external_event_id="manual-success-refund",
    )
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-6",
            "status": "refunded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.REFUNDED
    assert order.status == Order.Status.CANCELLED
    assert PaymentEvent.objects.filter(
        payment=payment,
        external_event_id="provider-event-6",
        new_status=Payment.Status.REFUNDED,
    ).exists()
