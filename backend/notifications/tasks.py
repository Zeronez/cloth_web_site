from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from config.celery import app
from notifications.models import NotificationAttempt, NotificationLog
from orders.models import Order


def _format_money(amount):
    return f"{amount:.2f} ₽"


def build_order_confirmation_message(order):
    subject = f"AnimeAttire: заказ #{order.id} оформлен"
    body = (
        f"Здравствуйте, {order.shipping_name}!\n\n"
        f"Спасибо за заказ #{order.id} в AnimeAttire.\n"
        f"Сумма заказа: {_format_money(order.total_amount)}.\n"
        "Мы приняли заказ и скоро начнем его обработку.\n\n"
        "Если у вас есть вопросы, ответьте на это письмо."
    )
    return subject, body


def _get_or_create_order_created_log(order, subject, body):
    defaults = {
        "recipient": order.user.email,
        "subject": subject,
        "body": body,
    }
    return NotificationLog.objects.get_or_create(
        order=order,
        notification_type=NotificationLog.Type.ORDER_CREATED,
        channel=NotificationLog.Channel.EMAIL,
        defaults=defaults,
    )


@app.task(name="notifications.send_order_confirmation_email")
def send_order_confirmation_email(order_id):
    order = Order.objects.select_related("user").get(id=order_id)
    subject, body = build_order_confirmation_message(order)

    with transaction.atomic():
        log, _ = _get_or_create_order_created_log(order, subject, body)
        log = NotificationLog.objects.select_for_update().get(id=log.id)
        if log.status == NotificationLog.Status.DELIVERED:
            return {"status": "skipped", "notification_log_id": log.id}

        log.status = NotificationLog.Status.PENDING
        log.recipient = order.user.email
        log.subject = subject
        log.body = body
        log.error_message = ""
        log.save(
            update_fields=[
                "status",
                "recipient",
                "subject",
                "body",
                "error_message",
                "updated_at",
            ]
        )

    try:
        delivered_count = send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
    except Exception as exc:
        NotificationAttempt.objects.create(
            notification=log,
            status=NotificationAttempt.Status.FAILED,
            error_message=str(exc),
        )
        NotificationLog.objects.filter(id=log.id).update(
            status=NotificationLog.Status.FAILED,
            error_message=str(exc),
            updated_at=timezone.now(),
        )
        raise

    NotificationAttempt.objects.create(
        notification=log,
        status=NotificationAttempt.Status.DELIVERED,
        provider_message_id=str(delivered_count),
    )
    NotificationLog.objects.filter(id=log.id).update(
        status=NotificationLog.Status.DELIVERED,
        delivered_at=timezone.now(),
        error_message="",
        updated_at=timezone.now(),
    )
    return {
        "status": "delivered",
        "notification_log_id": log.id,
        "delivered_count": delivered_count,
    }
