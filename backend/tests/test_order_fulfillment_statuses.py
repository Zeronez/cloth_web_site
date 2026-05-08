from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from catalog.models import (
    AnimeFranchise,
    Category,
    InventoryAdjustment,
    Product,
    ProductVariant,
)
from orders.models import Order
from orders.services import confirm_order_return_received, restore_order_stock
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


def create_order(user, **overrides):
    payload = {
        "user": user,
        "total_amount": Decimal("125.00"),
        **shipping_payload(),
    }
    payload.update(overrides)
    return Order.objects.create(**payload)


def create_payment_fixture(user):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = create_order(user)
    payment, _, _ = create_payment_session(
        user=user,
        order_id=order.id,
        payment_method_code=method.code,
        idempotency_key="order-fulfillment-payment",
    )
    return order, payment


def create_stocked_order(
    user, *, status=Order.Status.PAID, stock_quantity=0, quantity=1
):
    order = create_order(user, status=status)
    category = Category.objects.create(name=f"Stock Category {order.id}")
    franchise = AnimeFranchise.objects.create(name=f"Stock Franchise {order.id}")
    product = Product.objects.create(
        category=category,
        franchise=franchise,
        name=f"Stock Tee {order.id}",
        description="Stock restore fixture.",
        base_price=Decimal("125.00"),
        is_active=True,
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku=f"RESTOCK-{order.id}",
        size=ProductVariant.Size.M,
        color="Black",
        stock_quantity=stock_quantity,
        price_delta=Decimal("0.00"),
        is_active=True,
    )
    order.items.create(
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=quantity,
        price_at_purchase=variant.price,
    )
    return order, variant


def test_order_can_move_through_fulfillment_states(user):
    order = create_order(user, status=Order.Status.PAID)

    assert order.transition_to(Order.Status.PICKING) is True
    assert order.transition_to(Order.Status.PACKED) is True
    assert order.transition_to(Order.Status.SHIPPED) is True
    assert order.transition_to(Order.Status.DELIVERED) is True

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED
    assert order.is_terminal is True


def test_order_rejects_invalid_transition_from_pending_to_shipped(user):
    order = create_order(user)

    with pytest.raises(ValueError, match="Order cannot transition"):
        order.transition_to(Order.Status.SHIPPED)

    order.refresh_from_db()
    assert order.status == Order.Status.PENDING


def test_refund_after_shipment_marks_order_as_returned(api_client, user):
    order, payment = create_payment_fixture(user)
    payment.transition_to(
        Payment.Status.SUCCEEDED,
        event_type="manual_success",
        message="Marked as paid in test.",
        external_event_id="order-shipped-success",
    )
    order.transition_to(Order.Status.PAID)
    order.transition_to(Order.Status.PICKING)
    order.transition_to(Order.Status.PACKED)
    order.transition_to(Order.Status.SHIPPED)

    response = api_client.post(
        "/api/payments/webhooks/placeholder/",
        {
            "event_id": "provider-event-shipped-refund",
            "status": "refunded",
            "order_id": order.id,
            "payment_id": payment.id,
        },
        format="json",
    )

    assert response.status_code == 200
    order.refresh_from_db()
    payment.refresh_from_db()
    assert payment.status == Payment.Status.REFUNDED
    assert order.status == Order.Status.RETURNED


def test_order_detail_api_includes_russian_status_label(authenticated_client, user):
    order = create_order(user, status=Order.Status.PICKING)

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.PICKING
    assert response.data["status_label"] == "На сборке"


def test_restore_order_stock_is_idempotent(user):
    order, variant = create_stocked_order(user, stock_quantity=0, quantity=2)

    first_result = restore_order_stock(
        order=order,
        note=f"Возврат стока по заказу #{order.id} для теста идемпотентности.",
    )
    second_result = restore_order_stock(
        order=order,
        note=f"Повторный возврат стока по заказу #{order.id} не должен сработать.",
    )

    order.refresh_from_db()
    variant.refresh_from_db()
    assert first_result is True
    assert second_result is False
    assert order.stock_restored_at is not None
    assert variant.stock_quantity == 2
    adjustments = InventoryAdjustment.objects.filter(
        variant=variant,
        reason=InventoryAdjustment.Reason.RETURN,
    )
    assert adjustments.count() == 1
    assert adjustments.get().delta == 2


def test_confirm_order_return_received_requires_returned_status(user):
    order, _variant = create_stocked_order(
        user, status=Order.Status.SHIPPED, quantity=1
    )

    with pytest.raises(ValidationError):
        confirm_order_return_received(order=order)

    order.refresh_from_db()
    assert order.stock_restored_at is None


def test_confirm_order_return_received_restocks_returned_order_once(user):
    order, variant = create_stocked_order(
        user, status=Order.Status.RETURNED, stock_quantity=0, quantity=2
    )

    first_result = confirm_order_return_received(order=order)
    second_result = confirm_order_return_received(order=order)

    order.refresh_from_db()
    variant.refresh_from_db()
    assert first_result is True
    assert second_result is False
    assert order.stock_restored_at is not None
    assert variant.stock_quantity == 2
    assert (
        InventoryAdjustment.objects.filter(
            variant=variant,
            reason=InventoryAdjustment.Reason.RETURN,
        ).count()
        == 1
    )
