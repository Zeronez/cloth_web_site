import hashlib
import hmac

from django.conf import settings
from rest_framework.exceptions import PermissionDenied


DEFAULT_SIGNATURE_HEADER = "X-Payment-Signature"


def _signature_error(code, message):
    raise PermissionDenied({"webhook": {"code": code, "message": message}})


def _verify_bypass(*, provider_code, raw_body, headers):
    return {
        "provider": provider_code,
        "mode": "bypass",
        "header": "",
        "signature_checked": False,
    }


def _verify_hmac_sha256(*, provider_code, raw_body, headers):
    secrets = getattr(settings, "PAYMENT_WEBHOOK_SECRETS", {})
    signature_headers = getattr(settings, "PAYMENT_WEBHOOK_SIGNATURE_HEADERS", {})
    secret = secrets.get(provider_code, "")
    if not secret:
        _signature_error(
            "signature_not_configured",
            "Для этого платежного провайдера не настроен webhook secret.",
        )

    header_name = signature_headers.get(provider_code, DEFAULT_SIGNATURE_HEADER)
    received_signature = headers.get(header_name, "").strip()
    if not received_signature:
        _signature_error(
            "signature_missing",
            f"Отсутствует заголовок подписи {header_name}.",
        )

    expected_digest = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    accepted_values = (expected_digest, f"sha256={expected_digest}")
    if not any(
        hmac.compare_digest(received_signature, candidate)
        for candidate in accepted_values
    ):
        _signature_error(
            "signature_invalid",
            "Подпись webhook не прошла проверку.",
        )

    return {
        "provider": provider_code,
        "mode": "hmac_sha256",
        "header": header_name,
        "signature_checked": True,
    }


def get_webhook_signature_verifier(provider_code):
    bypass_providers = set(getattr(settings, "PAYMENT_WEBHOOK_BYPASS_PROVIDERS", ()))
    if provider_code in bypass_providers:
        return _verify_bypass
    return _verify_hmac_sha256


def verify_payment_webhook_signature(*, provider_code, raw_body, headers):
    verifier = get_webhook_signature_verifier(provider_code)
    return verifier(provider_code=provider_code, raw_body=raw_body, headers=headers)
