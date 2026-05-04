from dataclasses import dataclass, field
from urllib.parse import urlencode

from django.conf import settings

from payments.models import Payment


@dataclass(frozen=True)
class PaymentSessionResult:
    provider: str
    confirmation_url: str | None
    message: str
    external_payment_id: str = ""
    session_status: str = Payment.Status.SESSION_CREATED
    payload: dict = field(default_factory=dict)


class BasePaymentProviderAdapter:
    provider_code = ""
    supported_session_modes = ()

    def supports(self, session_mode):
        return session_mode in self.supported_session_modes

    def create_session(self, *, payment, method):
        raise NotImplementedError


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


_PLACEHOLDER = PlaceholderProviderAdapter()
_PROVIDERS = {
    "manual": _PLACEHOLDER,
    "placeholder": _PLACEHOLDER,
    "local": _PLACEHOLDER,
    "yookassa": YooKassaSandboxAdapter(),
}


def get_payment_provider(provider_code):
    return _PROVIDERS.get(provider_code)
