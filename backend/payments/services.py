from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod
from payments.providers import get_payment_provider


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


def _payment_webhook_error(code, message):
    return ValidationError({"webhook": {"code": code, "message": message}})


class PaymentWebhookConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "payment_webhook_conflict"
    default_detail = {
        "webhook": {
            "code": "payment_webhook_conflict",
            "message": "Конфликт при обработке webhook.",
        }
    }


def _sync_order_after_payment_status(payment, new_status):
    order = payment.order
    if new_status == Payment.Status.SUCCEEDED and order.status != Order.Status.PAID:
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
        return

    if new_status == Payment.Status.REFUNDED and order.status != Order.Status.CANCELLED:
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])


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
    provider = get_payment_provider(method.provider_code)
    if provider is None:
        raise _payment_session_error(
            "provider_not_configured",
            "Внешний платежный провайдер не подключен.",
        )
    if method.session_mode == PaymentMethod.SessionMode.NONE:
        raise _payment_session_error(
            "payment_session_disabled",
            "Для этого способа оплаты платежная сессия не создается.",
        )
    if not provider.supports(method.session_mode):
        raise _payment_session_error(
            "payment_session_unsupported",
            "Платежная сессия для этого провайдера настроена некорректно.",
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
            session = provider.create_session(payment=existing, method=method)
            return existing, session, False

    active_payment = (
        Payment.objects.select_for_update()
        .filter(order=order)
        .exclude(status__in=Payment.TERMINAL_STATUSES)
        .first()
    )
    if active_payment:
        session = provider.create_session(payment=active_payment, method=method)
        return active_payment, session, False

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

    session = provider.create_session(payment=payment, method=method)
    if (
        session.external_payment_id
        and payment.external_payment_id != session.external_payment_id
    ):
        payment.external_payment_id = session.external_payment_id
        payment.save(update_fields=["external_payment_id", "updated_at"])

    payment.transition_to(
        session.session_status,
        event_type="session_created",
        message=session.message,
        payload=session.payload,
    )
    return payment, session, True


def _locate_payment_for_webhook(
    *,
    provider_code,
    order_id,
    payment_id=None,
    external_payment_id="",
):
    payments = Payment.objects.select_for_update().select_related("order", "user")
    if payment_id is not None:
        payment = payments.filter(pk=payment_id).first()
    elif external_payment_id:
        payment = payments.filter(
            order_id=order_id,
            provider_code=provider_code,
            external_payment_id=external_payment_id,
        ).first()
        if payment is None:
            payment = payments.filter(
                order_id=order_id, provider_code=provider_code
            ).first()
    else:
        payment = payments.filter(
            order_id=order_id, provider_code=provider_code
        ).first()

    if payment is None:
        raise _payment_webhook_error("payment_not_found", "Платеж не найден.")
    if payment.order_id != order_id:
        raise PaymentWebhookConflict(
            {
                "webhook": {
                    "code": "order_mismatch",
                    "message": "Webhook ссылается на другой заказ.",
                }
            }
        )
    if payment.provider_code != provider_code:
        raise PaymentWebhookConflict(
            {
                "webhook": {
                    "code": "provider_mismatch",
                    "message": "Провайдер webhook не совпадает с платежом.",
                }
            }
        )
    if (
        external_payment_id
        and payment.external_payment_id
        and payment.external_payment_id != external_payment_id
    ):
        raise PaymentWebhookConflict(
            {
                "webhook": {
                    "code": "external_payment_mismatch",
                    "message": "Внешний идентификатор платежа не совпадает.",
                }
            }
        )
    return payment


@transaction.atomic
def process_payment_webhook(
    *,
    provider_code,
    event_id,
    status,
    order_id,
    payment_id=None,
    external_payment_id="",
    payload=None,
):
    payload = payload or {}
    payment = _locate_payment_for_webhook(
        provider_code=provider_code,
        order_id=order_id,
        payment_id=payment_id,
        external_payment_id=external_payment_id,
    )
    existing_event = PaymentEvent.objects.filter(
        payment=payment, external_event_id=event_id
    ).first()
    if existing_event is not None:
        return {
            "payment": payment,
            "event_id": event_id,
            "code": "event_replayed",
            "message": "Событие уже было обработано ранее.",
            "processed": False,
            "replayed": True,
            "conflict": False,
        }

    update_fields = []
    if external_payment_id and payment.external_payment_id != external_payment_id:
        payment.external_payment_id = external_payment_id
        update_fields.append("external_payment_id")

    if status == payment.status:
        if update_fields:
            payment.save(update_fields=[*update_fields, "updated_at"])
        PaymentEvent.objects.create(
            payment=payment,
            event_type="webhook_noop",
            previous_status=payment.status,
            new_status=payment.status,
            message="Webhook повторно подтвердил текущий статус платежа.",
            payload=payload,
            external_event_id=event_id,
        )
        return {
            "payment": payment,
            "event_id": event_id,
            "code": "status_unchanged",
            "message": "Статус платежа уже совпадает с webhook.",
            "processed": True,
            "replayed": False,
            "conflict": False,
        }

    if not payment.can_transition_to(status):
        raise PaymentWebhookConflict(
            {
                "webhook": {
                    "code": "invalid_transition",
                    "message": (
                        f"Нельзя перевести платеж из {payment.status} в {status}."
                    ),
                }
            }
        )

    if update_fields:
        payment.save(update_fields=[*update_fields, "updated_at"])

    payment.transition_to(
        status,
        event_type="webhook_status_update",
        message="Статус платежа обновлен из webhook.",
        payload=payload,
        external_event_id=event_id,
    )
    _sync_order_after_payment_status(payment, status)

    return {
        "payment": payment,
        "event_id": event_id,
        "code": "processed",
        "message": "Webhook успешно обработан.",
        "processed": True,
        "replayed": False,
        "conflict": False,
    }
