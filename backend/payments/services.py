from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod


def get_available_payment_methods():
    return PaymentMethod.objects.filter(is_active=True).order_by("sort_order", "name")


def resolve_payment_method(code):
    try:
        return get_available_payment_methods().get(code=code)
    except PaymentMethod.DoesNotExist as exc:
        raise ValidationError(
            {
                "payment_method_code": {
                    "code": "payment_method_unavailable",
                    "message": "Способ оплаты недоступен.",
                }
            }
        ) from exc


def _payment_session_error(code, message):
    return ValidationError({"payment": {"code": code, "message": message}})


SAFE_PLACEHOLDER_PROVIDERS = {"manual", "placeholder", "local"}


@transaction.atomic
def create_payment_session(*, user, order_id, payment_method_code, idempotency_key=""):
    order = (
        Order.objects.select_for_update()
        .select_related("user")
        .filter(pk=order_id, user=user)
        .first()
    )
    if order is None:
        raise _payment_session_error("order_not_found", "Заказ не найден.")
    if order.status != Order.Status.PENDING:
        raise _payment_session_error(
            "order_not_payable", "Заказ сейчас нельзя оплатить."
        )
    if order.total_amount <= 0:
        raise _payment_session_error(
            "invalid_amount", "Сумма заказа должна быть больше нуля."
        )

    method = resolve_payment_method(payment_method_code)
    if method.session_mode != PaymentMethod.SessionMode.PLACEHOLDER:
        raise _payment_session_error(
            "payment_session_disabled",
            "Для этого способа оплаты платежная сессия не создается.",
        )
    if method.provider_code not in SAFE_PLACEHOLDER_PROVIDERS:
        raise _payment_session_error(
            "provider_not_configured",
            "Внешний платежный провайдер не подключен.",
        )
    if method.currency != "RUB":
        raise _payment_session_error(
            "currency_unsupported", "Пока поддерживается только валюта RUB."
        )

    if idempotency_key:
        existing = Payment.objects.filter(
            user=user, idempotency_key=idempotency_key
        ).first()
        if existing:
            if existing.order_id != order.id or existing.method_code != method.code:
                raise _payment_session_error(
                    "idempotency_conflict",
                    "Ключ идемпотентности уже использован для другого платежа.",
                )
            return existing, False

    active_payment = (
        Payment.objects.select_for_update()
        .filter(order=order)
        .exclude(status__in=Payment.TERMINAL_STATUSES)
        .first()
    )
    if active_payment:
        return active_payment, False

    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency=method.currency,
        idempotency_key=idempotency_key,
        session_expires_at=timezone.now() + timedelta(minutes=20),
    )
    PaymentEvent.objects.create(
        payment=payment,
        event_type="created",
        previous_status="",
        new_status=payment.status,
        message="Платеж создан.",
        payload={"order_id": order.id},
    )
    payment.transition_to(
        Payment.Status.SESSION_CREATED,
        event_type="session_created",
        message="Локальная платежная сессия создана. Внешний провайдер не подключен.",
        payload={"provider": "placeholder"},
    )
    return payment, True
