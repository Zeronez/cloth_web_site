from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from delivery.models import DeliveryMethod, OrderDeliverySnapshot
from delivery.services import create_order_delivery_snapshot, create_shipment_for_order
from orders.models import Order, OrderItem
from payments.models import Payment, PaymentMethod


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


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="AdminPass!2026",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


def create_delivery_method(code):
    return DeliveryMethod.objects.create(
        code=code,
        name="Курьер по Москве",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
    )


def create_order_with_snapshot(
    user, product_factory, *, status, sku, provider_code="manual"
):
    product = product_factory(
        name=f"Admin {sku}",
        base_price="40.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=status,
        **shipping_payload(),
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=2,
        price_at_purchase=Decimal("40.00"),
    )
    snapshot = create_order_delivery_snapshot(
        order,
        create_delivery_method(f"courier-{sku.lower()}"),
        shipping_payload(),
    )
    snapshot.provider_code = provider_code
    snapshot.save(update_fields=["provider_code"])
    return order


def create_payment(order, *, status):
    method = PaymentMethod.objects.create(
        code=f"manual-{order.id}",
        name="Банковская карта",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
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


def test_order_admin_changelist_exposes_fulfillment_summary(
    admin_client, user, product_factory
):
    paid_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.PAID, sku="ADMIN-PAID-M"
    )
    packed_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.PACKED, sku="ADMIN-PACK-M"
    )
    handoff_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.PACKED, sku="ADMIN-HAND-M"
    )
    create_shipment_for_order(
        order=handoff_order,
        provider_code="cdek",
        external_shipment_id="SHIP-ADMIN-1",
        track_number="TRACK-ADMIN-1",
    )
    issue_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.SHIPPED, sku="ADMIN-ISSUE-M"
    )
    issue_order.delivery_snapshot.tracking_status = (
        OrderDeliverySnapshot.TrackingStatus.FAILED
    )
    issue_order.delivery_snapshot.save(update_fields=["tracking_status"])
    create_payment(issue_order, status=Payment.Status.FAILED)
    create_payment(paid_order, status=Payment.Status.SUCCEEDED)
    create_payment(packed_order, status=Payment.Status.SUCCEEDED)
    create_payment(handoff_order, status=Payment.Status.SUCCEEDED)

    response = admin_client.get(reverse("admin:orders_order_changelist"))

    assert response.status_code == 200
    summary = response.context_data["fulfillment_summary"]
    assert summary["paid_ready"] == 1
    assert summary["packing_queue"] == 2
    assert summary["awaiting_shipment"] == 2
    assert summary["handoff_queue"] == 1
    assert summary["delivery_issues"] == 1


def test_order_admin_queue_mode_picking_returns_actionable_orders(
    admin_client, user, product_factory
):
    picking_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.PICKING, sku="ADMIN-PICK-M"
    )
    create_payment(picking_order, status=Payment.Status.SUCCEEDED)
    packed_order = create_order_with_snapshot(
        user, product_factory, status=Order.Status.PACKED, sku="ADMIN-PACKED-M"
    )

    response = admin_client.get(
        f"{reverse('admin:orders_order_changelist')}?queue=picking"
    )

    assert response.status_code == 200
    assert response.context_data["queue_mode"] == "picking"
    queue_orders = response.context_data["queue_orders"]
    order_ids = [row["order"].id for row in queue_orders]
    assert picking_order.id in order_ids
    assert packed_order.id not in order_ids
    assert any(row["next_step"] == "Проверить SKU и упаковать" for row in queue_orders)
