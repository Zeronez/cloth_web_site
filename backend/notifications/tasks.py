from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from config.celery import app
from notifications.models import NotificationAttempt, NotificationLog
from orders.models import Order

RETRYABLE_NOTIFICATION_EXCEPTIONS = (ConnectionError, OSError, TimeoutError)


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


def _notification_retry_countdown(retry_number):
    countdown = settings.CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS * (
        2 ** (retry_number - 1)
    )
    return min(countdown, settings.CELERY_NOTIFICATION_RETRY_MAX_SECONDS)


@app.task(
    bind=True,
    name="notifications.send_order_confirmation_email",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=settings.CELERY_NOTIFICATION_MAX_RETRIES,
)
def send_order_confirmation_email(self, order_id):
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
        log.dead_lettered_at = None
        log.save(
            update_fields=[
                "status",
                "recipient",
                "subject",
                "body",
                "error_message",
                "dead_lettered_at",
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

        is_retryable = isinstance(exc, RETRYABLE_NOTIFICATION_EXCEPTIONS)
        retry_number = self.request.retries + 1

        if is_retryable and retry_number <= self.max_retries:
            countdown = _notification_retry_countdown(retry_number)
            NotificationAttempt.objects.create(
                notification=log,
                status=NotificationAttempt.Status.RETRY_SCHEDULED,
                error_message=(
                    f"retry #{retry_number} scheduled in {countdown}s: {exc}"
                ),
            )
            NotificationLog.objects.filter(id=log.id).update(
                status=NotificationLog.Status.PENDING,
                error_message=str(exc),
                updated_at=timezone.now(),
            )
            raise self.retry(exc=exc, countdown=countdown)

        terminal_status = (
            NotificationLog.Status.DEAD_LETTERED
            if is_retryable and retry_number > self.max_retries
            else NotificationLog.Status.FAILED
        )
        NotificationLog.objects.filter(id=log.id).update(
            status=terminal_status,
            error_message=str(exc),
            dead_lettered_at=(
                timezone.now()
                if terminal_status == NotificationLog.Status.DEAD_LETTERED
                else None
            ),
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
        dead_lettered_at=None,
        error_message="",
        updated_at=timezone.now(),
    )
    return {
        "status": "delivered",
        "notification_log_id": log.id,
        "delivered_count": delivered_count,
    }
