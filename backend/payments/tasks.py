from django.conf import settings
from django.db import transaction
from django.utils import timezone

from config.celery import app
from orders.models import Order
from orders.services import transition_order_status
from payments.models import Payment
from payments.providers import fetch_provider_payment_status
from payments.services import process_payment_webhook

LOCAL_EXPIRY_PROVIDER_CODES = {"manual", "placeholder", "local"}


def _expire_payment_locally(payment):
    previous_stock_restored_at = payment.order.stock_restored_at
    payment.transition_to(
        Payment.Status.EXPIRED,
        event_type="session_expired",
        message="Payment session expired before customer completed checkout.",
        payload={"order_id": payment.order_id, "source": "local_timeout_task"},
    )
    transition_order_status(
        order=payment.order,
        new_status=Order.Status.CANCELLED,
        restock_on_cancel=True,
        restock_note=(
            f"Released stock after local payment expiry for order #{payment.order_id}."
        ),
    )
    payment.order.refresh_from_db()
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "payment_status": Payment.Status.EXPIRED,
        "order_status": payment.order.status,
        "stock_restored": (
            previous_stock_restored_at is None
            and payment.order.stock_restored_at is not None
        ),
        "source": "local_expiry",
    }


def _apply_provider_status(payment, fetch_result):
    previous_stock_restored_at = payment.order.stock_restored_at
    result = process_payment_webhook(
        provider_code=payment.provider_code,
        event_id=fetch_result.event_id,
        status=fetch_result.status,
        order_id=payment.order_id,
        payment_id=payment.id,
        external_payment_id=fetch_result.external_payment_id
        or payment.external_payment_id,
        payload=fetch_result.payload,
    )
    payment.refresh_from_db()
    payment.order.refresh_from_db()
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "payment_status": payment.status,
        "order_status": payment.order.status,
        "stock_restored": (
            previous_stock_restored_at is None
            and payment.order.stock_restored_at is not None
        ),
        "source": "provider_reconciliation",
        "provider_processed": result["processed"],
        "provider_code": result["code"],
    }


@app.task(
    bind=True,
    name="payments.expire_stale_payment_sessions",
    acks_late=True,
    reject_on_worker_lost=True,
)
def expire_stale_payment_sessions_task(self):
    now = timezone.now()
    expired = []
    skipped = []
    candidate_ids = list(
        Payment.objects.filter(
            status__in=[Payment.Status.PENDING, Payment.Status.SESSION_CREATED],
            session_expires_at__isnull=False,
            session_expires_at__lte=now,
        )
        .order_by("session_expires_at", "id")
        .values_list("id", flat=True)[: settings.PAYMENT_EXPIRATION_BATCH_SIZE]
    )

    for payment_id in candidate_ids:
        with transaction.atomic():
            payment = (
                Payment.objects.select_for_update()
                .select_related("order")
                .filter(id=payment_id)
                .first()
            )
            if payment is None:
                continue
            if payment.status not in {
                Payment.Status.PENDING,
                Payment.Status.SESSION_CREATED,
            }:
                skipped.append(payment_id)
                continue
            if payment.session_expires_at is None or payment.session_expires_at > now:
                skipped.append(payment_id)
                continue
            if payment.order.status != Order.Status.PENDING:
                skipped.append(payment_id)
                continue

            fetch_result = fetch_provider_payment_status(
                provider_code=payment.provider_code,
                payment=payment,
            )
            if fetch_result is not None:
                expired.append(_apply_provider_status(payment, fetch_result))
                continue

            if payment.provider_code not in LOCAL_EXPIRY_PROVIDER_CODES:
                skipped.append(payment_id)
                continue

            expired.append(_expire_payment_locally(payment))

    return {
        "status": "ok",
        "expired_count": len(expired),
        "skipped_count": len(skipped),
        "expired": expired,
        "skipped_payment_ids": skipped,
    }
