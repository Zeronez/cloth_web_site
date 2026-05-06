import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from catalog.models import InventoryAdjustment, ProductVariant
from catalog.stock import LOW_STOCK_THRESHOLD, adjust_variant_stock
from users.staff_roles import ROLE_INVENTORY_MANAGER


pytestmark = pytest.mark.django_db


@pytest.fixture
def inventory_manager(db):
    call_command("sync_staff_roles")
    user = get_user_model().objects.create_user(
        username="inventory-manager",
        email="inventory@example.com",
        password="InventoryPass!2026",
        is_staff=True,
    )
    user.groups.add(Group.objects.get(name=ROLE_INVENTORY_MANAGER))
    return user


def test_adjust_variant_stock_creates_audit_and_updates_quantity(user, product_factory):
    product = product_factory(
        name="Inventory Tee",
        variants=[{"sku": "INV-TEE-M", "stock_quantity": 5}],
    )
    variant = product.variants.get()

    updated_variant, adjustment = adjust_variant_stock(
        variant_id=variant.id,
        delta=4,
        reason=InventoryAdjustment.Reason.RESTOCK,
        performed_by=user,
        note="Поставка от локального поставщика.",
    )

    assert updated_variant.stock_quantity == 9
    assert adjustment.previous_quantity == 5
    assert adjustment.new_quantity == 9
    assert adjustment.delta == 4
    assert adjustment.performed_by == user
    assert adjustment.note == "Поставка от локального поставщика."


def test_adjust_variant_stock_rejects_negative_result_without_audit(
    user, product_factory
):
    product = product_factory(
        name="Inventory Hoodie",
        variants=[{"sku": "INV-HOOD-L", "stock_quantity": 2}],
    )
    variant = product.variants.get()

    with pytest.raises(ValidationError):
        adjust_variant_stock(
            variant_id=variant.id,
            delta=-3,
            reason=InventoryAdjustment.Reason.DAMAGE,
            performed_by=user,
            note="Списание брака.",
        )

    variant.refresh_from_db()
    assert variant.stock_quantity == 2
    assert InventoryAdjustment.objects.count() == 0


def test_inventory_adjustment_changes_low_stock_visibility(product_factory):
    product = product_factory(
        name="Low Stock Tee",
        variants=[{"sku": "LOW-TEE-S", "stock_quantity": LOW_STOCK_THRESHOLD + 1}],
    )
    variant = product.variants.get()

    adjust_variant_stock(
        variant_id=variant.id,
        delta=-2,
        reason=InventoryAdjustment.Reason.COUNT,
        note="После пересчёта на складе.",
    )

    low_stock_skus = set(
        ProductVariant.objects.filter(
            stock_quantity__lte=LOW_STOCK_THRESHOLD
        ).values_list("sku", flat=True)
    )
    assert "LOW-TEE-S" in low_stock_skus


def test_checkout_respects_manual_inventory_adjustment(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Adjusted Stock Tee",
        variants=[{"sku": "ADJ-TEE-M", "stock_quantity": 5}],
    )
    variant = product.variants.get()

    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 3},
        format="json",
    )
    adjust_variant_stock(
        variant_id=variant.id,
        delta=-4,
        reason=InventoryAdjustment.Reason.COUNT,
        note="Фактический остаток ниже после сверки.",
    )

    response = authenticated_client.post(
        "/api/orders/checkout/",
        {
            "shipping_name": "QA Shopper",
            "shipping_phone": "+15551234567",
            "shipping_country": "RU",
            "shipping_city": "Moscow",
            "shipping_postal_code": "101000",
            "shipping_line1": "Test street 1",
            "shipping_line2": "",
        },
        format="json",
    )

    assert response.status_code == 400
    variant.refresh_from_db()
    assert variant.stock_quantity == 1


def test_inventory_manager_role_can_access_adjustment_admin_but_not_orders(
    client, inventory_manager, product_factory
):
    product = product_factory(
        name="Role Tee",
        variants=[{"sku": "ROLE-TEE-M", "stock_quantity": 5}],
    )
    variant = product.variants.get()
    client.force_login(inventory_manager)

    adjustment_response = client.get(reverse("admin:catalog_inventoryadjustment_add"))
    variant_response = client.get(reverse("admin:catalog_productvariant_changelist"))
    orders_response = client.get(reverse("admin:orders_order_changelist"))

    assert adjustment_response.status_code == 200
    assert variant_response.status_code == 200
    assert orders_response.status_code != 200

    create_response = client.post(
        reverse("admin:catalog_inventoryadjustment_add"),
        {
            "variant": variant.id,
            "reason": InventoryAdjustment.Reason.RESTOCK,
            "delta": 2,
            "note": "Добили полку новым тиражом.",
        },
        follow=True,
    )

    assert create_response.status_code == 200
    variant.refresh_from_db()
    assert variant.stock_quantity == 7
    adjustment = InventoryAdjustment.objects.get(variant=variant)
    assert adjustment.performed_by == inventory_manager
