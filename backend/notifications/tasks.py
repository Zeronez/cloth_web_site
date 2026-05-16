from datetime import timedelta
from email.utils import parseaddr
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from config.celery import app
from config.logging import sanitize_log_text
from notifications.models import NotificationAttempt, NotificationLog
from orders.models import Order

RETRYABLE_NOTIFICATION_EXCEPTIONS = (
    ConnectionError,
    OSError,
    TimeoutError,
    SMTPException,
)


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


def _notification_processing_lease_seconds():
    return settings.CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS


def _notification_processing_is_stale(processing_started_at):
    if processing_started_at is None:
        return True
    lease_started_before = timezone.now() - timedelta(
        seconds=_notification_processing_lease_seconds()
    )
    return processing_started_at < lease_started_before


def _notification_lease_retry_countdown(processing_started_at):
    if processing_started_at is None:
        return 1
    lease_expires_at = processing_started_at + timedelta(
        seconds=_notification_processing_lease_seconds()
    )
    remaining = int((lease_expires_at - timezone.now()).total_seconds())
    return max(1, remaining)


def _notification_message_id(log):
    _display_name, from_email = parseaddr(settings.DEFAULT_FROM_EMAIL)
    domain = from_email.partition("@")[2] or "example.com"
    key = f"order-{log.order_id}-{log.notification_type}-{log.channel}"
    return f"<{key}@{domain}>"


def _build_order_confirmation_email(log):
    message_id = _notification_message_id(log)
    return EmailMultiAlternatives(
        subject=log.subject,
        body=log.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[log.recipient],
        headers={
            "Message-ID": message_id,
            "X-Notification-Idempotency-Key": message_id.strip("<>"),
        },
    )


def _mark_notification_retry_scheduled(log, *, exc, retry_number, countdown):
    safe_error = sanitize_log_text(exc, limit=255)
    NotificationAttempt.objects.create(
        notification=log,
        status=NotificationAttempt.Status.RETRY_SCHEDULED,
        provider_message_id=_notification_message_id(log),
        error_message=sanitize_log_text(
            f"retry #{retry_number} scheduled in {countdown}s: {safe_error}",
            limit=255,
        ),
    )
    NotificationLog.objects.filter(id=log.id).update(
        status=NotificationLog.Status.PENDING,
        error_message=safe_error,
        processing_started_at=None,
        updated_at=timezone.now(),
    )


def _mark_notification_terminal_failure(log, *, exc, dead_lettered):
    status = (
        NotificationLog.Status.DEAD_LETTERED
        if dead_lettered
        else NotificationLog.Status.FAILED
    )
    attempts_count = log.attempts.exclude(
        status=NotificationAttempt.Status.RETRY_SCHEDULED
    ).count()
    safe_error = sanitize_log_text(exc, limit=255)
    message = (
        f"dead-lettered after {attempts_count} delivery attempts: {safe_error}"
        if dead_lettered
        else safe_error
    )
    NotificationLog.objects.filter(id=log.id).update(
        status=status,
        error_message=sanitize_log_text(message, limit=255),
        dead_lettered_at=timezone.now() if dead_lettered else None,
        processing_started_at=None,
        updated_at=timezone.now(),
    )


@app.task(
    bind=True,
    name="notifications.send_order_confirmation_email",
    acks_late=True,
    reject_on_worker_lost=True,
)
def send_order_confirmation_email(self, order_id):
    order = Order.objects.select_related("user").get(id=order_id)
    subject, body = build_order_confirmation_message(order)

    with transaction.atomic():
        log, _ = _get_or_create_order_created_log(order, subject, body)
        log = NotificationLog.objects.select_for_update().get(id=log.id)
        if log.status == NotificationLog.Status.DELIVERED:
            return {
                "status": "skipped",
                "notification_log_id": log.id,
                "message_id": _notification_message_id(log),
            }

        if (
            log.processing_started_at is not None
            and not _notification_processing_is_stale(log.processing_started_at)
        ):
            raise self.retry(
                countdown=_notification_lease_retry_countdown(
                    log.processing_started_at
                ),
                max_retries=settings.CELERY_NOTIFICATION_MAX_RETRIES,
            )

        log.status = NotificationLog.Status.PENDING
        log.recipient = order.user.email
        log.subject = subject
        log.body = body
        log.error_message = ""
        log.dead_lettered_at = None
        log.processing_started_at = timezone.now()
        log.save(
            update_fields=[
                "status",
                "recipient",
                "subject",
                "body",
                "error_message",
                "dead_lettered_at",
                "processing_started_at",
                "updated_at",
            ]
        )

    try:
        delivered_count = _build_order_confirmation_email(log).send(fail_silently=False)
    except Exception as exc:
        safe_error = sanitize_log_text(exc, limit=255)
        NotificationAttempt.objects.create(
            notification=log,
            status=NotificationAttempt.Status.FAILED,
            provider_message_id=_notification_message_id(log),
            error_message=safe_error,
        )

        is_retryable = isinstance(exc, RETRYABLE_NOTIFICATION_EXCEPTIONS)
        retry_number = self.request.retries + 1

        if is_retryable and retry_number <= settings.CELERY_NOTIFICATION_MAX_RETRIES:
            countdown = _notification_retry_countdown(retry_number)
            _mark_notification_retry_scheduled(
                log,
                exc=exc,
                retry_number=retry_number,
                countdown=countdown,
            )
            raise self.retry(
                exc=exc,
                countdown=countdown,
                max_retries=settings.CELERY_NOTIFICATION_MAX_RETRIES,
            )

        _mark_notification_terminal_failure(
            log,
            exc=exc,
            dead_lettered=(
                is_retryable and retry_number > settings.CELERY_NOTIFICATION_MAX_RETRIES
            ),
        )
        raise

    NotificationAttempt.objects.create(
        notification=log,
        status=NotificationAttempt.Status.DELIVERED,
        provider_message_id=_notification_message_id(log),
    )
    NotificationLog.objects.filter(id=log.id).update(
        status=NotificationLog.Status.DELIVERED,
        delivered_at=timezone.now(),
        dead_lettered_at=None,
        error_message="",
        processing_started_at=None,
        updated_at=timezone.now(),
    )
    return {
        "status": "delivered",
        "notification_log_id": log.id,
        "delivered_count": delivered_count,
        "message_id": _notification_message_id(log),
    }
