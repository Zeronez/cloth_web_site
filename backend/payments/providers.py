from dataclasses import dataclass, field
from urllib.parse import urlencode

from django.conf import settings
from rest_framework.exceptions import ValidationError

from payments.models import Payment


@dataclass(frozen=True)
class PaymentSessionResult:
    provider: str
    confirmation_url: str | None
    message: str
    external_payment_id: str = ""
    session_status: str = Payment.Status.SESSION_CREATED
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentStatusFetchResult:
    status: str
    event_id: str
    external_payment_id: str = ""
    payload: dict = field(default_factory=dict)


class BasePaymentProviderAdapter:
    provider_code = ""
    supported_session_modes = ()

    def supports(self, session_mode):
        return session_mode in self.supported_session_modes

    def create_session(self, *, payment, method):
        raise NotImplementedError

    def normalize_webhook_payload(self, payload):
        return payload

    def fetch_payment_status(self, *, payment, external_payment_id=""):
        return None


class PlaceholderProviderAdapter(BasePaymentProviderAdapter):
    provider_code = "placeholder"
    supported_session_modes = ("placeholder",)

    def create_session(self, *, payment, method):
        return PaymentSessionResult(
            provider=method.provider_code,
            confirmation_url=None,
            message="Платежная сессия создана локально. Внешний провайдер не подключен.",
            payload={"provider": method.provider_code},
        )


class YooKassaSandboxAdapter(BasePaymentProviderAdapter):
    provider_code = "yookassa"
    supported_session_modes = ("redirect",)

    STATUS_MAPPING = {
        "pending": Payment.Status.PENDING,
        "waiting_for_capture": Payment.Status.AUTHORIZED,
        "succeeded": Payment.Status.SUCCEEDED,
        "failed": Payment.Status.FAILED,
        "canceled": Payment.Status.CANCELLED,
        "cancelled": Payment.Status.CANCELLED,
        "refunded": Payment.Status.REFUNDED,
    }

    def create_session(self, *, payment, method):
        external_payment_id = payment.external_payment_id or (
            f"yookassa-sandbox-{payment.pk}"
        )
        base_url = getattr(settings, "PAYMENT_PROVIDER_CONFIRMATION_URLS", {}).get(
            "yookassa", "https://yookassa.example/checkout"
        )
        return_base_url = getattr(
            settings,
            "PAYMENT_PROVIDER_RETURN_BASE_URL",
            "http://localhost:3000/checkout/return",
        )
        return_url = f"{return_base_url}?" + urlencode(
            {
                "provider": "yookassa",
                "order_id": payment.order_id,
                "payment_id": payment.pk,
                "external_payment_id": external_payment_id,
            }
        )
        confirmation_url = f"{base_url.rstrip('/')}/{external_payment_id}?" + urlencode(
            {"return_url": return_url}
        )
        return PaymentSessionResult(
            provider="yookassa",
            confirmation_url=confirmation_url,
            external_payment_id=external_payment_id,
            message="Платежная сессия YooKassa подготовлена в sandbox-режиме.",
            payload={
                "provider": "yookassa",
                "mode": "sandbox",
                "confirmation_url": confirmation_url,
                "return_url": return_url,
            },
        )

    def normalize_webhook_payload(self, payload):
        if not isinstance(payload, dict):
            return payload
        if "object" not in payload or "event" not in payload:
            return payload

        payment_object = payload.get("object") or {}
        metadata = payment_object.get("metadata") or {}
        raw_status = str(payment_object.get("status", "")).strip().lower()
        normalized_status = self.STATUS_MAPPING.get(raw_status)
        external_payment_id = str(payment_object.get("id", "")).strip()
        order_id = metadata.get("order_id") or payload.get("order_id")
        payment_id = metadata.get("payment_id") or payload.get("payment_id")
        event_name = str(payload.get("event", "")).strip()
        event_id = str(payload.get("id") or payload.get("event_id") or "").strip()

        if not normalized_status:
            raise ValidationError(
                {
                    "webhook": {
                        "code": "webhook_status_unsupported",
                        "message": "YooKassa webhook содержит неподдерживаемый статус.",
                    }
                }
            )
        if not external_payment_id:
            raise ValidationError(
                {
                    "webhook": {
                        "code": "webhook_external_payment_missing",
                        "message": "YooKassa webhook не содержит внешний идентификатор платежа.",
                    }
                }
            )
        if not order_id and not payment_id:
            raise ValidationError(
                {
                    "webhook": {
                        "code": "webhook_payment_reference_missing",
                        "message": "YooKassa webhook не содержит ссылку на заказ или платеж.",
                    }
                }
            )

        normalized = {
            "event_id": event_id or f"{event_name}:{external_payment_id}:{raw_status}",
            "provider": "yookassa",
            "status": normalized_status,
            "external_payment_id": external_payment_id,
            "payload": {
                "provider_payload": payload,
                "event": event_name,
                "object": payment_object,
            },
        }
        if order_id:
            normalized["order_id"] = int(order_id)
        if payment_id:
            normalized["payment_id"] = int(payment_id)
        return normalized

    def fetch_payment_status(self, *, payment, external_payment_id=""):
        effective_external_id = external_payment_id or payment.external_payment_id
        if not effective_external_id:
            return None

        provider_statuses = getattr(settings, "PAYMENT_PROVIDER_STATUS_OVERRIDES", {})
        provider_overrides = provider_statuses.get("yookassa", {})
        raw_status = provider_overrides.get(effective_external_id)
        if not raw_status:
            return None

        normalized_status = self.STATUS_MAPPING.get(str(raw_status).strip().lower())
        if not normalized_status:
            raise ValidationError(
                {
                    "payment": {
                        "code": "provider_status_unsupported",
                        "message": "Sandbox-статус провайдера не поддерживается.",
                    }
                }
            )

        return PaymentStatusFetchResult(
            status=normalized_status,
            event_id=f"return-sync:{effective_external_id}:{normalized_status}",
            external_payment_id=effective_external_id,
            payload={
                "provider": "yookassa",
                "status_source": "sandbox_override",
                "raw_status": raw_status,
            },
        )


_PLACEHOLDER = PlaceholderProviderAdapter()
_PROVIDERS = {
    "manual": _PLACEHOLDER,
    "placeholder": _PLACEHOLDER,
    "local": _PLACEHOLDER,
    "yookassa": YooKassaSandboxAdapter(),
}


def get_payment_provider(provider_code):
    return _PROVIDERS.get(provider_code)


def normalize_payment_webhook_payload(*, provider_code, payload):
    provider = get_payment_provider(provider_code)
    if provider is None:
        return payload
    return provider.normalize_webhook_payload(payload)


def fetch_provider_payment_status(*, provider_code, payment, external_payment_id=""):
    provider = get_payment_provider(provider_code)
    if provider is None:
        return None
    return provider.fetch_payment_status(
        payment=payment,
        external_payment_id=external_payment_id,
    )
