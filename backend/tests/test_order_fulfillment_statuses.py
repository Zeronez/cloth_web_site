from decimal import Decimal

import pytest

from orders.models import Order
from payments.models import Payment, PaymentMethod
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


def create_order(user, **overrides):
    payload = {
        "user": user,
        "total_amount": Decimal("125.00"),
        **shipping_payload(),
    }
    payload.update(overrides)
    return Order.objects.create(**payload)


def create_payment_fixture(user):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = create_order(user)
    payment, _, _ = create_payment_session(
        user=user,
        order_id=order.id,
        payment_method_code=method.code,
        idempotency_key="order-fulfillment-payment",
    )
    return order, payment


def test_order_can_move_through_fulfillment_states(user):
    order = create_order(user, status=Order.Status.PAID)

    assert order.transition_to(Order.Status.PICKING) is True
    assert order.transition_to(Order.Status.PACKED) is True
    assert order.transition_to(Order.Status.SHIPPED) is True
    assert order.transition_to(Order.Status.DELIVERED) is True

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED
    assert order.is_terminal is True


def test_order_rejects_invalid_transition_from_pending_to_shipped(user):
    order = create_order(user)

    with pytest.raises(ValueError, match="Order cannot transition"):
        order.transition_to(Order.Status.SHIPPED)

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING


def test_refund_after_shipment_marks_order_as_returned(api_client, user):
    order, payment = create_payment_fixture(user)
    payment.transition_to(
        Payment.Status.SUCCEEDED,
        event_type="manual_success",
        message="Marked as paid in test.",
        external_event_id="order-shipped-success",
    )
    order.transition_to(Order.Status.PAID)
    order.transition_to(Order.Status.PICKING)
    order.transition_to(Order.Status.PACKED)
    order.transition_to(Order.Status.SHIPPED)

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-shipped-refund",
            "status": "refunded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 200
    order.refresh_from_db()
    payment.refresh_from_db()
    assert payment.status == Payment.Status.REFUNDED
    assert order.status == Order.Status.RETURNED


def test_order_detail_api_includes_russian_status_label(authenticated_client, user):
    order = create_order(user, status=Order.Status.PICKING)

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.PICKING
    assert response.data["status_label"] == "На сборке"
