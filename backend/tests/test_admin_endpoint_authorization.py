from decimal import Decimal

import pytest
from django.urls import reverse

from orders.models import Order, OrderItem
from support.models import ContactRequest


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


def create_order(user, product_factory, *, sku="AUTH-ORDER-M"):
    product = product_factory(
        name=f"Auth {sku}",
        base_price="55.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("110.00"),
        status=Order.Status.PAID,
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
        price_at_purchase=Decimal("55.00"),
    )
    return order, variant


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:index",
        "admin:orders_order_changelist",
        "admin:payments_payment_changelist",
        "admin:catalog_product_changelist",
        "admin:catalog_productvariant_changelist",
        "admin:catalog_inventoryadjustment_add",
        "admin:support_contactrequest_changelist",
        "admin:users_user_changelist",
        "admin:audit_auditlog_changelist",
        "admin:delivery_orderdeliverysnapshot_changelist",
    ],
)
def test_regular_user_cannot_open_staff_admin_routes(client, user, url_name):
    client.force_login(user)

    response = client.get(reverse(url_name))

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_regular_user_cannot_open_admin_custom_packing_slip_view(
    client, user, product_factory
):
    order, _variant = create_order(user, product_factory, sku="AUTH-SLIP-M")
    order.internal_note = "Только для staff."
    order.save(update_fields=["internal_note", "updated_at"])
    client.force_login(user)

    response = client.get(reverse("admin:orders_order_packing_slip", args=[order.id]))

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
    assert "AUTH-SLIP-M" not in response.content.decode("utf-8", errors="ignore")


def test_regular_user_cannot_execute_staff_admin_action(
    client, user, product_factory
):
    order, _variant = create_order(user, product_factory, sku="AUTH-ACTION-M")
    client.force_login(user)

    response = client.post(
        reverse("admin:orders_order_changelist"),
        {
            "action": "mark_cancelled",
            "_selected_action": [str(order.id)],
        },
    )

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
    order.refresh_from_db()
    assert order.status == Order.Status.PAID


def test_regular_user_cannot_create_inventory_adjustment_via_admin(
    client, user, product_factory
):
    product = product_factory(
        name="Auth Inventory Tee",
        variants=[{"sku": "AUTH-INV-M", "stock_quantity": 5}],
    )
    variant = product.variants.get()
    client.force_login(user)

    response = client.post(
        reverse("admin:catalog_inventoryadjustment_add"),
        {
            "variant": variant.id,
            "reason": "restock",
            "delta": 3,
            "note": "Недопустимая попытка regular user.",
        },
    )

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
    variant.refresh_from_db()
    assert variant.stock_quantity == 5
    assert variant.inventory_adjustments.count() == 0


def test_regular_user_cannot_open_support_contact_request_admin(client, user):
    contact_request = ContactRequest.objects.create(
        name="QA Shopper",
        email="shopper@example.com",
        topic=ContactRequest.Topic.ORDER,
        order_number="AA-42",
        message="Где мой заказ?",
        admin_notes="Внутренняя заметка staff.",
    )
    client.force_login(user)

    response = client.get(
        reverse("admin:support_contactrequest_change", args=[contact_request.id])
    )

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
