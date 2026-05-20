from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from payments.models import Payment, PaymentMethod


pytestmark = pytest.mark.django_db


def create_paid_order(user, product_factory, *, sku="REFUND-SKU"):
    product = product_factory(
        name="Refund Tee",
        base_price="50.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        currency="RUB",
        total_amount=Decimal("100.00"),
        items_subtotal_amount=Decimal("100.00"),
        delivery_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        status=Order.Status.PAID,
        shipping_name="QA Shopper",
        shipping_phone="+79990000000",
        shipping_country="RU",
        shipping_city="Moscow",
        shipping_postal_code="101000",
        shipping_line1="Refund street 1",
        shipping_line2="",
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=2,
        price_at_purchase=Decimal("50.00"),
    )
    return order


def create_payment(order, *, status=Payment.Status.SUCCEEDED):
    method = PaymentMethod.objects.create(
        code=f"card-{order.id}",
        name="Card",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
        currency="RUB",
    )
    return Payment.objects.create(
        order=order,
        user=order.user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency="RUB",
        status=status,
    )


def test_staff_can_refund_payment_partially_and_fully(
    api_client, user, product_factory
):
    staff_user = get_user_model().objects.create_user(
        username="staff-refund",
        email="staff-refund@example.com",
        password="AdminPass!2026",
        is_staff=True,
    )
    api_client.force_authenticate(user=staff_user)

    order = create_paid_order(user, product_factory)
    payment = create_payment(order, status=Payment.Status.SUCCEEDED)

    partial_response = api_client.post(
        f"/api/v1/payments/{payment.id}/refund/",
        {"amount": "40.00"},
        format="json",
    )
    assert partial_response.status_code == 200
    payment.refresh_from_db()
    assert payment.refunded_amount == Decimal("40.00")
    assert payment.status == Payment.Status.SUCCEEDED

    final_response = api_client.post(
        f"/api/v1/payments/{payment.id}/refund/",
        {"amount": "60.00"},
        format="json",
    )
    assert final_response.status_code == 200
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.refunded_amount == Decimal("100.00")
    assert payment.status == Payment.Status.REFUNDED
    assert order.status == Order.Status.CANCELLED
