from decimal import Decimal

import pytest

from orders.models import Order
from payments.models import Payment, PaymentMethod
from payments.services import create_payment_session


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Test street 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


def create_redirect_payment(user, *, provider_code="yookassa"):
    method = PaymentMethod.objects.create(
        code=f"{provider_code}-card",
        name=f"{provider_code} card",
        provider_code=provider_code,
        session_mode="redirect",
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    payment, _, _ = create_payment_session(
        user=user,
        order_id=order.id,
        payment_method_code=method.code,
        idempotency_key=f"return-status-{provider_code}",
    )
    return order, payment


def test_authenticated_user_can_resolve_own_payment_return_status(
    authenticated_client, user, settings
):
    settings.PAYMENT_PROVIDER_CONFIRMATION_URLS = {
        "yookassa": "https://pay.example.test/checkout"
    }
    settings.PAYMENT_PROVIDER_RETURN_BASE_URL = (
        "https://animeattire.example/checkout/return"
    )
    order, payment = create_redirect_payment(user)

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa", "external_payment_id": payment.external_payment_id},
    )

    assert response.status_code == 200
    assert response.data["provider"] == "yookassa"
    assert response.data["return_state"] == "awaiting_webhook"
    assert response.data["can_retry"] is True
    assert response.data["order"]["id"] == order.id
    assert response.data["payment"]["id"] == payment.id
    assert response.data["confirmation_url"].startswith(
        "https://pay.example.test/checkout/yookassa-sandbox-"
    )


def test_foreign_user_cannot_resolve_another_users_payment_return_status(
    authenticated_client, other_user
):
    _, payment = create_redirect_payment(other_user)

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert response.status_code == 404
    assert response.data["payment"]["code"] == "payment_not_found"


def test_return_status_rejects_provider_mismatch(authenticated_client, user):
    _, payment = create_redirect_payment(user)

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "placeholder"},
    )

    assert response.status_code == 409
    assert response.data["webhook"]["code"] == "provider_mismatch"


def test_return_status_rejects_external_payment_mismatch(authenticated_client, user):
    _, payment = create_redirect_payment(user)

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa", "external_payment_id": "wrong-id"},
    )

    assert response.status_code == 409
    assert response.data["webhook"]["code"] == "external_payment_mismatch"


def test_return_status_after_success_webhook_returns_paid_state(
    authenticated_client, user
):
    order, payment = create_redirect_payment(user)
    payment.transition_to(
        Payment.Status.SUCCEEDED,
        event_type="manual_success",
        message="Marked as paid in test.",
        external_event_id="success-return",
    )
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert response.status_code == 200
    assert response.data["return_state"] == "paid"
    assert response.data["can_retry"] is False
    assert response.data["confirmation_url"] is None


def test_return_status_after_failed_payment_returns_retry_available(
    authenticated_client, user
):
    _, payment = create_redirect_payment(user)
    payment.transition_to(
        Payment.Status.FAILED,
        event_type="manual_failed",
        message="Marked as failed in test.",
        external_event_id="failed-return",
    )

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert response.status_code == 200
    assert response.data["return_state"] == "retry_available"
    assert response.data["can_retry"] is True
    assert response.data["confirmation_url"] is None


def test_return_status_can_reconcile_sandbox_success_via_provider_fetch(
    authenticated_client, user, settings
):
    _, payment = create_redirect_payment(user)
    settings.PAYMENT_PROVIDER_STATUS_OVERRIDES = {
        "yookassa": {
            payment.external_payment_id: "succeeded",
        }
    }

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert response.status_code == 200
    assert response.data["return_state"] == "paid"
    assert response.data["can_retry"] is False
    assert "sandbox-ответу провайдера" in response.data["message"]

    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED


def test_return_status_can_reconcile_sandbox_authorized_without_paid_order(
    authenticated_client, user, settings
):
    order, payment = create_redirect_payment(user)
    settings.PAYMENT_PROVIDER_STATUS_OVERRIDES = {
        "yookassa": {
            payment.external_payment_id: "waiting_for_capture",
        }
    }

    response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert response.status_code == 200
    assert response.data["return_state"] == "awaiting_webhook"
    assert response.data["can_retry"] is True

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == Payment.Status.AUTHORIZED
    assert order.status == Order.Status.PENDING


def test_return_status_provider_fetch_is_idempotent_on_repeat_calls(
    authenticated_client, user, settings
):
    _, payment = create_redirect_payment(user)
    settings.PAYMENT_PROVIDER_STATUS_OVERRIDES = {
        "yookassa": {
            payment.external_payment_id: "succeeded",
        }
    }

    first_response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )
    second_response = authenticated_client.get(
        f"/api/payments/{payment.id}/return-status/",
        {"provider": "yookassa"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED
    assert (
        payment.events.filter(
            external_event_id=f"return-sync:{payment.external_payment_id}:succeeded"
        ).count()
        == 1
    )
