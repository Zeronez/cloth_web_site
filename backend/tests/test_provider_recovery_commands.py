from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from rest_framework.exceptions import ValidationError

from delivery.models import DeliveryMethod, OrderDeliverySnapshot
from delivery.services import create_order_delivery_snapshot, create_shipment_for_order
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


def create_redirect_payment(user, *, provider_code="yookassa"):
    method = PaymentMethod.objects.create(
        code=f"{provider_code}-card",
        name=f"{provider_code} card",
        provider_code=provider_code,
        session_mode=PaymentMethod.SessionMode.REDIRECT,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    payment, _, _ = create_payment_session(
        user=user,
        order_id=order.id,
        payment_method_code=method.code,
        idempotency_key=f"reconcile-{provider_code}-{order.id}",
    )
    return order, payment


def create_delivery_order(user, *, provider_code="cdek"):
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=Order.Status.PAID,
        **shipping_payload(),
    )
    method = DeliveryMethod.objects.create(
        code=f"{provider_code}-delivery-{order.id}",
        name="Курьерская доставка",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
    )
    snapshot = create_order_delivery_snapshot(order, method, shipping_payload())
    snapshot.provider_code = provider_code
    snapshot.save(update_fields=["provider_code"])
    create_shipment_for_order(
        order=order,
        provider_code=provider_code,
        external_shipment_id=f"{provider_code}-shipment-{order.id}",
        track_number=f"{provider_code.upper()}-{order.id}",
    )
    return order


def test_reconcilepayments_applies_provider_success_override(user, settings):
    order, payment = create_redirect_payment(user)
    settings.PAYMENT_PROVIDER_STATUS_OVERRIDES = {
        "yookassa": {payment.external_payment_id: "succeeded"}
    }
    stdout = StringIO()

    call_command("reconcilepayments", payment_id=payment.id, stdout=stdout)

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED
    assert order.status == Order.Status.PAID
    assert "processed -> succeeded" in stdout.getvalue()


def test_reconcilepayments_keeps_state_on_provider_error(user, monkeypatch):
    order, payment = create_redirect_payment(user)
    stdout = StringIO()
    stderr = StringIO()

    def fail_fetch(**kwargs):
        raise ValidationError(
            {
                "payment": {
                    "code": "provider_status_unsupported",
                    "message": "Sandbox status is unsupported.",
                }
            }
        )

    monkeypatch.setattr(
        "payments.management.commands.reconcilepayments.fetch_provider_payment_status",
        fail_fetch,
    )

    call_command(
        "reconcilepayments",
        payment_id=payment.id,
        stdout=stdout,
        stderr=stderr,
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.SESSION_CREATED
    assert order.status == Order.Status.PENDING
    assert "failed=1" in stdout.getvalue()
    assert "reconciliation failed" in stderr.getvalue()


def test_reconciletracking_updates_snapshot_from_provider_override(user, settings):
    order = create_delivery_order(user)
    snapshot = order.delivery_snapshot
    snapshot.refresh_from_db()
    settings.DELIVERY_PROVIDER_TRACKING_OVERRIDES = {
        "cdek": {
            snapshot.external_shipment_id: {
                "status": "delivered",
                "location": "Москва",
                "message": "Заказ доставлен.",
            }
        }
    }
    stdout = StringIO()

    call_command("reconciletracking", order_id=order.id, stdout=stdout)

    order.refresh_from_db()
    snapshot.refresh_from_db()
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.DELIVERED
    assert order.status == Order.Status.DELIVERED
    assert "tracking updated -> delivered" in stdout.getvalue()


def test_reconciletracking_keeps_state_on_provider_error(user, settings):
    order = create_delivery_order(user)
    snapshot = order.delivery_snapshot
    snapshot.refresh_from_db()
    settings.DELIVERY_PROVIDER_TRACKING_OVERRIDES = {
        "cdek": {
            snapshot.external_shipment_id: {
                "status": "mystery-status",
                "location": "Москва",
            }
        }
    }
    stdout = StringIO()
    stderr = StringIO()

    call_command(
        "reconciletracking",
        order_id=order.id,
        stdout=stdout,
        stderr=stderr,
    )

    order.refresh_from_db()
    snapshot.refresh_from_db()
    assert snapshot.tracking_status == OrderDeliverySnapshot.TrackingStatus.CREATED
    assert order.status == Order.Status.PAID
    assert "failed=1" in stdout.getvalue()
    assert "tracking reconciliation failed" in stderr.getvalue()
