from decimal import Decimal

import pytest

from cart.models import Cart
from delivery.models import DeliveryMethod, OrderDeliverySnapshot
from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod
from payments.services import create_payment_session


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "US",
        "shipping_city": "New York",
        "shipping_postal_code": "10001",
        "shipping_line1": "11 Test Avenue",
        "shipping_line2": "Apt 5",
    }
    payload.update(overrides)
    return payload


def test_available_delivery_and_payment_methods_return_active_only(api_client):
    DeliveryMethod.objects.create(
        code="courier-msk",
        name="Курьер по Москве",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        sort_order=10,
    )
    DeliveryMethod.objects.create(
        code="archived-delivery",
        name="Архивная доставка",
        is_active=False,
    )
    PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
        sort_order=10,
    )
    PaymentMethod.objects.create(
        code="archived-payment",
        name="Архивная оплата",
        is_active=False,
    )

    delivery_response = api_client.get("/api/delivery-methods/")
    payment_response = api_client.get("/api/payment-methods/")

    assert delivery_response.status_code == 200
    assert [item["code"] for item in delivery_response.data["results"]] == [
        "courier-msk"
    ]
    assert delivery_response.data["results"][0]["kind_label"] == "Курьер"

    assert payment_response.status_code == 200
    assert [item["code"] for item in payment_response.data["results"]] == ["local-card"]
    assert payment_response.data["results"][0]["session_mode_label"] == (
        "Локальная сессия"
    )


def test_checkout_snapshots_delivery_method_and_adds_delivery_price(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Delivery Foundation Tee",
        base_price="40.00",
        variants=[
            {
                "sku": "DELIVERY-TEE-BLK-M",
                "stock_quantity": 3,
            }
        ],
    )
    variant = product.variants.get()
    method = DeliveryMethod.objects.create(
        code="courier-msk",
        name="Курьер по Москве",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        estimated_days_min=1,
        estimated_days_max=2,
    )
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 2},
        format="json",
    )

    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(delivery_method_code=method.code),
        format="json",
    )

    assert checkout_response.status_code == 201
    assert checkout_response.data["total_amount"] == "430.00"
    assert checkout_response.data["delivery"]["method_code"] == "courier-msk"
    assert checkout_response.data["delivery"]["method_name"] == "Курьер по Москве"
    assert checkout_response.data["delivery"]["price_amount"] == "350.00"

    order = Order.objects.get(user=user)
    snapshot = OrderDeliverySnapshot.objects.get(order=order)
    assert order.total_amount == Decimal("430.00")
    assert snapshot.delivery_method == method
    assert snapshot.recipient_name == "QA Shopper"
    assert Cart.objects.get(user=user).items.count() == 0


def test_checkout_uses_first_active_delivery_method_when_code_is_omitted(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Delivery Optional Tee",
        base_price="40.00",
        variants=[
            {
                "sku": "DELIVERY-OPT-TEE-M",
                "stock_quantity": 1,
            }
        ],
    )
    variant = product.variants.get()
    method = DeliveryMethod.objects.create(
        code="pickup-point",
        name="Пункт выдачи",
        kind=DeliveryMethod.Kind.PICKUP,
        price_amount=Decimal("0.00"),
        estimated_days_min=2,
        estimated_days_max=4,
        sort_order=5,
    )
    DeliveryMethod.objects.create(
        code="courier-backup",
        name="Курьер резерв",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("300.00"),
        sort_order=10,
    )
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 201
    assert checkout_response.data["total_amount"] == "40.00"
    assert checkout_response.data["delivery"]["method_code"] == method.code
    assert checkout_response.data["delivery"]["method_name"] == method.name
    assert checkout_response.data["delivery"]["price_amount"] == "0.00"

    order = Order.objects.get(user=user)
    snapshot = OrderDeliverySnapshot.objects.get(order=order)
    assert snapshot.method_code == method.code
    assert snapshot.price_amount == Decimal("0.00")


def test_payment_session_placeholder_is_safe_and_idempotent(authenticated_client, user):
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )

    create_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": order.id,
            "payment_method_code": method.code,
            "idempotency_key": "checkout-123",
        },
        format="json",
    )

    assert create_response.status_code == 201
    assert create_response.data["created"] is True
    assert create_response.data["provider"] == "placeholder"
    assert create_response.data["confirmation_url"] is None
    assert "Внешний провайдер не подключен" in create_response.data["message"]
    assert create_response.data["payment"]["status"] == "session_created"
    assert create_response.data["payment"]["status_label"] == "Сессия создана"

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING

    payment = Payment.objects.get(order=order)
    assert payment.amount == Decimal("125.00")
    assert payment.method_code == "local-card"
    assert list(
        PaymentEvent.objects.filter(payment=payment).values_list(
            "event_type", "new_status"
        )
    ) == [
        ("created", "pending"),
        ("session_created", "session_created"),
    ]

    retry_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": order.id,
            "payment_method_code": method.code,
            "idempotency_key": "checkout-123",
        },
        format="json",
    )

    assert retry_response.status_code == 200
    assert retry_response.data["created"] is False
    assert retry_response.data["payment"]["id"] == create_response.data["payment"]["id"]
    assert Payment.objects.filter(order=order).count() == 1


def test_payment_sessions_are_scoped_to_the_authenticated_user(
    authenticated_client, user, other_user
):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    own_order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(shipping_name="QA Shopper"),
    )
    other_order = Order.objects.create(
        user=other_user,
        total_amount=Decimal("145.00"),
        **shipping_payload(shipping_name="Other Shopper"),
    )
    own_payment, _ = create_payment_session(
        user=user,
        order_id=own_order.id,
        payment_method_code=method.code,
        idempotency_key="own-session",
    )
    other_payment, _ = create_payment_session(
        user=other_user,
        order_id=other_order.id,
        payment_method_code=method.code,
        idempotency_key="other-session",
    )

    list_response = authenticated_client.get("/api/payments/")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.data["results"]] == [own_payment.id]

    own_detail_response = authenticated_client.get(f"/api/payments/{own_payment.id}/")
    other_detail_response = authenticated_client.get(
        f"/api/payments/{other_payment.id}/"
    )

    assert own_detail_response.status_code == 200
    assert own_detail_response.data["id"] == own_payment.id
    assert other_detail_response.status_code == 404

    foreign_order_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": other_order.id,
            "payment_method_code": method.code,
            "idempotency_key": "foreign-order",
        },
        format="json",
    )

    assert foreign_order_response.status_code == 400
    assert foreign_order_response.data["payment"]["code"] == "order_not_found"


def test_payment_session_idempotency_key_conflicts_across_orders(
    authenticated_client, user
):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    first_order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(shipping_name="QA Shopper"),
    )
    second_order = Order.objects.create(
        user=user,
        total_amount=Decimal("145.00"),
        **shipping_payload(shipping_name="QA Shopper"),
    )

    first_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": first_order.id,
            "payment_method_code": method.code,
            "idempotency_key": "shared-key",
        },
        format="json",
    )
    conflict_response = authenticated_client.post(
        "/api/payments/sessions/",
        {
            "order_id": second_order.id,
            "payment_method_code": method.code,
            "idempotency_key": "shared-key",
        },
        format="json",
    )

    assert first_response.status_code == 201
    assert conflict_response.status_code == 400
    assert conflict_response.data["payment"]["code"] == "idempotency_conflict"
    assert Payment.objects.filter(user=user, idempotency_key="shared-key").count() == 1


def test_payment_session_rejects_unconfigured_external_provider(
    authenticated_client, user
):
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    PaymentMethod.objects.create(
        code="yookassa-card",
        name="YooKassa card",
        provider_code="yookassa",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )

    response = authenticated_client.post(
        "/api/payments/sessions/",
        {"order_id": order.id, "payment_method_code": "yookassa-card"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["payment"]["code"] == "provider_not_configured"
    assert response.data["payment"]["message"] == (
        "Внешний платежный провайдер не подключен."
    )
    assert not Payment.objects.filter(order=order).exists()
