from decimal import Decimal

import pytest
from celery.exceptions import Retry
from django.core import mail

from notifications.models import NotificationAttempt, NotificationLog
from notifications.tasks import _notification_message_id, send_order_confirmation_email
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
    assert log.processing_started_at is None
    assert log.attempts.filter(status=NotificationAttempt.Status.DELIVERED).count() == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].extra_headers["Message-ID"] == _notification_message_id(log)
    assert mail.outbox[0].extra_headers[
        "X-Notification-Idempotency-Key"
    ] == _notification_message_id(log).strip("<>")


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
    assert second_result["message_id"] == first_result["message_id"]
    assert (
        NotificationLog.objects.filter(
            order=order,
            notification_type=NotificationLog.Type.ORDER_CREATED,
            status=NotificationLog.Status.DELIVERED,
        ).count()
        == 1
    )
    log = NotificationLog.objects.get(order=order)
    assert log.processing_started_at is None
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


def test_order_confirmation_failed_send_is_logged(user, monkeypatch, settings):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("270.00"),
        **shipping_payload(),
    )
    settings.CELERY_NOTIFICATION_MAX_RETRIES = 0

    class FailingEmail:
        def send(self, fail_silently=False):
            raise RuntimeError("SMTP provider is unavailable")

    def raise_provider_error(*args, **kwargs):
        return FailingEmail()

    monkeypatch.setattr(
        "notifications.tasks._build_order_confirmation_email",
        raise_provider_error,
    )

    with pytest.raises(RuntimeError, match="SMTP provider is unavailable"):
        send_order_confirmation_email.delay(order.id).get()

    log = NotificationLog.objects.get(order=order)
    assert log.status == NotificationLog.Status.FAILED
    assert log.dead_lettered_at is None
    assert log.processing_started_at is None
    assert "SMTP provider is unavailable" in log.error_message
    attempt = log.attempts.get()
    assert attempt.status == NotificationAttempt.Status.FAILED
    assert attempt.provider_message_id == _notification_message_id(log)
    assert "SMTP provider is unavailable" in attempt.error_message


def test_notification_failure_redacts_pii_from_persisted_error_message(
    user, monkeypatch, settings
):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("270.00"),
        **shipping_payload(),
    )
    settings.CELERY_NOTIFICATION_MAX_RETRIES = 0

    class FailingEmail:
        def send(self, fail_silently=False):
            raise RuntimeError(
                "SMTP provider is unavailable for shopper@example.com token=abc123"
            )

    monkeypatch.setattr(
        "notifications.tasks._build_order_confirmation_email",
        lambda log: FailingEmail(),
    )

    with pytest.raises(RuntimeError, match="SMTP provider is unavailable"):
        send_order_confirmation_email.delay(order.id).get()

    log = NotificationLog.objects.get(order=order)
    attempt = log.attempts.get()
    assert "shopper@example.com" not in log.error_message
    assert "abc123" not in log.error_message
    assert "shopper@example.com" not in attempt.error_message
    assert "abc123" not in attempt.error_message


def test_order_confirmation_retryable_failure_can_recover(user, monkeypatch):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("295.00"),
        **shipping_payload(),
    )

    class FailingEmail:
        def send(self, fail_silently=False):
            raise OSError("SMTP temporarily unavailable")

    monkeypatch.setattr(
        "notifications.tasks._build_order_confirmation_email",
        lambda log: FailingEmail(),
    )

    def fake_retry(*args, **kwargs):
        raise Retry()

    monkeypatch.setattr(send_order_confirmation_email, "retry", fake_retry)

    send_order_confirmation_email.push_request(retries=0, id="notif-recovery-1")
    try:
        with pytest.raises(Retry):
            send_order_confirmation_email.run(order.id)
    finally:
        send_order_confirmation_email.pop_request()

    monkeypatch.undo()
    result = send_order_confirmation_email.delay(order.id).get()

    log = NotificationLog.objects.get(order=order)
    assert result["status"] == "delivered"
    assert log.status == NotificationLog.Status.DELIVERED
    assert log.dead_lettered_at is None
    assert log.processing_started_at is None
    assert list(log.attempts.values_list("status", flat=True)) == [
        NotificationAttempt.Status.FAILED,
        NotificationAttempt.Status.RETRY_SCHEDULED,
        NotificationAttempt.Status.DELIVERED,
    ]
    assert len(mail.outbox) == 1


def test_order_confirmation_retryable_failure_schedules_retry(user, monkeypatch):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("310.00"),
        **shipping_payload(),
    )
    countdowns = []

    def fake_retry(*args, **kwargs):
        countdowns.append(kwargs["countdown"])
        raise Retry()

    class FailingEmail:
        def send(self, fail_silently=False):
            raise OSError("SMTP temporarily unavailable")

    monkeypatch.setattr(
        "notifications.tasks._build_order_confirmation_email",
        lambda log: FailingEmail(),
    )
    monkeypatch.setattr(send_order_confirmation_email, "retry", fake_retry)

    send_order_confirmation_email.push_request(retries=0, id="notif-retry-1")
    try:
        with pytest.raises(Retry):
            send_order_confirmation_email.run(order.id)
    finally:
        send_order_confirmation_email.pop_request()

    log = NotificationLog.objects.get(order=order)
    assert log.status == NotificationLog.Status.PENDING
    assert log.dead_lettered_at is None
    assert log.processing_started_at is None
    assert "SMTP temporarily unavailable" in log.error_message
    assert countdowns == [30]
    assert list(log.attempts.values_list("status", flat=True)) == [
        NotificationAttempt.Status.FAILED,
        NotificationAttempt.Status.RETRY_SCHEDULED,
    ]


def test_order_confirmation_retryable_failure_moves_to_dead_letter(user, monkeypatch):
    clear_outbox()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("330.00"),
        **shipping_payload(),
    )

    class FailingEmail:
        def send(self, fail_silently=False):
            raise OSError("SMTP gateway still unavailable")

    monkeypatch.setattr(
        "notifications.tasks._build_order_confirmation_email",
        lambda log: FailingEmail(),
    )

    send_order_confirmation_email.push_request(
        retries=3,
        id="notif-dead-letter-1",
    )
    try:
        with pytest.raises(OSError, match="SMTP gateway still unavailable"):
            send_order_confirmation_email.run(order.id)
    finally:
        send_order_confirmation_email.pop_request()

    log = NotificationLog.objects.get(order=order)
    assert log.status == NotificationLog.Status.DEAD_LETTERED
    assert log.dead_lettered_at is not None
    assert log.processing_started_at is None
    assert "dead-lettered after 1 delivery attempts" in log.error_message
    assert list(log.attempts.values_list("status", flat=True)) == [
        NotificationAttempt.Status.FAILED,
    ]
