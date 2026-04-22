from decimal import Decimal

import pytest
from django.core import mail

from notifications.models import NotificationAttempt, NotificationLog
from notifications.tasks import send_order_confirmation_email
from orders.models import Order


pytestmark = pytest.mark.django_db


def clear_outbox():
    if hasattr(mail, "outbox"):
        mail.outbox.clear()
    else:
        mail.outbox = []


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


def test_checkout_sends_order_confirmation_in_eager_mode(
    authenticated_client, user, product_factory, django_capture_on_commit_callbacks
):
    clear_outbox()
    product = product_factory(
        name="Notification Tee",
        base_price="49.90",
        variants=[{"sku": "NOTIFY-TEE-M", "stock_quantity": 2}],
    )
    variant = product.variants.get()
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    with django_capture_on_commit_callbacks(execute=True):
        response = authenticated_client.post(
            "/api/orders/checkout/",
            shipping_payload(),
            format="json",
        )

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    log = NotificationLog.objects.get(
        order=order,
        notification_type=NotificationLog.Type.ORDER_CREATED,
        channel=NotificationLog.Channel.EMAIL,
    )
    assert log.status == NotificationLog.Status.DELIVERED
    assert log.recipient == user.email
    assert log.delivered_at is not None
    assert log.attempts.filter(status=NotificationAttempt.Status.DELIVERED).count() == 1
    assert len(mail.outbox) == 1


def test_order_confirmation_task_is_idempotent(user):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )

    first_result = send_order_confirmation_email.delay(order.id).get()
    second_result = send_order_confirmation_email.delay(order.id).get()

    assert first_result["status"] == "delivered"
    assert second_result["status"] == "skipped"
    assert (
        NotificationLog.objects.filter(
            order=order,
            notification_type=NotificationLog.Type.ORDER_CREATED,
            status=NotificationLog.Status.DELIVERED,
        ).count()
        == 1
    )
    log = NotificationLog.objects.get(order=order)
    assert log.attempts.filter(status=NotificationAttempt.Status.DELIVERED).count() == 1
    assert len(mail.outbox) == 1


def test_order_confirmation_email_body_includes_order_id_and_total(user):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("430.00"),
        **shipping_payload(),
    )

    send_order_confirmation_email.delay(order.id).get()

    message = mail.outbox[0]
    assert f"заказ #{order.id}" in message.subject
    assert f"заказ #{order.id}" in message.body
    assert "430.00" in message.body


def test_order_confirmation_failed_send_is_logged(user, monkeypatch):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("270.00"),
        **shipping_payload(),
    )

    def raise_provider_error(*args, **kwargs):
        raise RuntimeError("SMTP provider is unavailable")

    monkeypatch.setattr("notifications.tasks.send_mail", raise_provider_error)

    with pytest.raises(RuntimeError, match="SMTP provider is unavailable"):
        send_order_confirmation_email.delay(order.id).get()

    log = NotificationLog.objects.get(order=order)
    assert log.status == NotificationLog.Status.FAILED
    assert "SMTP provider is unavailable" in log.error_message
    attempt = log.attempts.get()
    assert attempt.status == NotificationAttempt.Status.FAILED
    assert "SMTP provider is unavailable" in attempt.error_message
