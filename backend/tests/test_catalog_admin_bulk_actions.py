from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from audit.models import AuditLog
from catalog.models import InventoryAdjustment, ProductVariant
from users.staff_roles import ROLE_INVENTORY_MANAGER


pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="bulk-admin",
        email="bulk-admin@example.com",
        password="AdminPass!2026",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


@pytest.fixture
def inventory_manager(db):
    call_command("sync_staff_roles")
    user = get_user_model().objects.create_user(
        username="bulk-inventory-manager",
        email="bulk-inventory@example.com",
        password="InventoryPass!2026",
        is_staff=True,
    )
    user.groups.add(Group.objects.get(name=ROLE_INVENTORY_MANAGER))
    return user


def post_action(client, url_name, action, object_ids):
    return client.post(
        reverse(url_name),
        {
            "action": action,
            "_selected_action": [str(object_id) for object_id in object_ids],
        },
        follow=True,
    )


def test_product_admin_bulk_price_action_updates_selected_products_with_audit(
    admin_client, product_factory
):
    first = product_factory(
        name="Bulk Price Tee",
        base_price="100.00",
        variants=[{"sku": "BULK-PRICE-1"}],
    )
    second = product_factory(
        name="Bulk Price Hoodie",
        base_price="200.00",
        variants=[{"sku": "BULK-PRICE-2"}],
    )
    untouched = product_factory(
        name="Bulk Price Untouched",
        base_price="300.00",
        variants=[{"sku": "BULK-PRICE-3"}],
    )

    response = post_action(
        admin_client,
        "admin:catalog_product_changelist",
        "increase_selected_product_prices_10_percent",
        [first.id, second.id],
    )

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    untouched.refresh_from_db()
    assert first.base_price == Decimal("110.00")
    assert second.base_price == Decimal("220.00")
    assert untouched.base_price == Decimal("300.00")
    logs = AuditLog.objects.filter(
        model="product",
        metadata__admin_action="increase_selected_product_prices_10_percent",
    ).order_by("object_id")
    assert logs.count() == 2
    assert logs[0].changes["base_price"] == {"old": "100.00", "new": "110.00"}
    assert logs[0].metadata["selected_count"] == 2


def test_product_admin_bulk_price_keeps_variant_price_delta(
    admin_client, product_factory
):
    product = product_factory(
        name="Bulk Price Delta",
        base_price="100.00",
        variants=[{"sku": "BULK-DELTA-1", "price_delta": "20.00"}],
    )
    variant = product.variants.get()

    response = post_action(
        admin_client,
        "admin:catalog_product_changelist",
        "increase_selected_product_prices_10_percent",
        [product.id],
    )

    assert response.status_code == 200
    product.refresh_from_db()
    variant.refresh_from_db()
    assert product.base_price == Decimal("110.00")
    assert variant.price_delta == Decimal("20.00")
    assert variant.price == Decimal("130.00")


def test_product_admin_bulk_status_action_updates_selected_products_with_audit(
    admin_client, product_factory
):
    first = product_factory(name="Bulk Status A", variants=[{"sku": "BULK-STATUS-A"}])
    second = product_factory(name="Bulk Status B", variants=[{"sku": "BULK-STATUS-B"}])
    untouched = product_factory(
        name="Bulk Status C", variants=[{"sku": "BULK-STATUS-C"}]
    )

    response = post_action(
        admin_client,
        "admin:catalog_product_changelist",
        "deactivate_selected_products",
        [first.id, second.id],
    )

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    untouched.refresh_from_db()
    assert first.is_active is False
    assert second.is_active is False
    assert untouched.is_active is True
    logs = AuditLog.objects.filter(
        model="product", metadata__admin_action="deactivate_selected_products"
    )
    assert logs.count() == 2
    assert {log.changes["is_active"]["new"] for log in logs} == {False}


def test_product_admin_archive_action_archives_products_and_deactivates_variants(
    admin_client, product_factory
):
    product = product_factory(
        name="Archive Capsule Jacket",
        variants=[
            {"sku": "ARCHIVE-CAPSULE-BLK-M", "color": "Black"},
            {"sku": "ARCHIVE-CAPSULE-WHT-L", "color": "White"},
        ],
    )

    response = post_action(
        admin_client,
        "admin:catalog_product_changelist",
        "archive_selected_products",
        [product.id],
    )

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.archived_at is not None
    assert product.is_active is False
    assert product.is_featured is False
    assert not ProductVariant.objects.filter(product=product, is_active=True).exists()
    log = AuditLog.objects.get(
        model="product", metadata__admin_action="archive_selected_products"
    )
    assert log.changes["archived_at"]["old"] is None
    assert log.changes["archived_at"]["new"]
    assert log.changes["is_active"]["new"] is False


def test_variant_admin_bulk_stock_action_creates_adjustments_and_audit(
    admin_client, admin_user, product_factory
):
    product = product_factory(
        name="Bulk Stock",
        variants=[
            {"sku": "BULK-STOCK-A", "stock_quantity": 5, "color": "Black"},
            {"sku": "BULK-STOCK-B", "stock_quantity": 1, "color": "White"},
        ],
    )
    first = product.variants.get(sku="BULK-STOCK-A")
    second = product.variants.get(sku="BULK-STOCK-B")

    response = post_action(
        admin_client,
        "admin:catalog_productvariant_changelist",
        "restock_selected_variants_by_5",
        [first.id, second.id],
    )

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.stock_quantity == 10
    assert second.stock_quantity == 6
    adjustments = InventoryAdjustment.objects.order_by("variant__sku")
    assert adjustments.count() == 2
    assert [adjustment.delta for adjustment in adjustments] == [5, 5]
    assert {adjustment.performed_by for adjustment in adjustments} == {admin_user}
    logs = AuditLog.objects.filter(
        model="inventoryadjustment",
        metadata__admin_action="restock_selected_variants_by_5",
    )
    assert logs.count() == 2
    assert {log.metadata["selected_count"] for log in logs} == {2}
    assert {log.snapshot["note"] for log in logs} == {"[redacted]"}


def test_variant_admin_write_off_skips_sku_without_stock(admin_client, product_factory):
    product = product_factory(
        name="Bulk Write Off",
        variants=[
            {"sku": "BULK-WRITE-A", "stock_quantity": 0, "color": "Black"},
            {"sku": "BULK-WRITE-B", "stock_quantity": 2, "color": "White"},
        ],
    )
    empty = product.variants.get(sku="BULK-WRITE-A")
    stocked = product.variants.get(sku="BULK-WRITE-B")

    response = post_action(
        admin_client,
        "admin:catalog_productvariant_changelist",
        "write_off_selected_variants_by_1",
        [empty.id, stocked.id],
    )

    assert response.status_code == 200
    empty.refresh_from_db()
    stocked.refresh_from_db()
    assert empty.stock_quantity == 0
    assert stocked.stock_quantity == 1
    assert InventoryAdjustment.objects.count() == 1
    log = AuditLog.objects.get(
        model="inventoryadjustment",
        metadata__admin_action="write_off_selected_variants_by_1",
    )
    assert log.metadata["skipped_count"] == 1


def test_variant_admin_bulk_status_action_does_not_change_product(
    admin_client, product_factory
):
    product = product_factory(
        name="Bulk Variant Status",
        variants=[
            {"sku": "BULK-VAR-A", "color": "Black"},
            {"sku": "BULK-VAR-B", "color": "White"},
        ],
    )
    variant_ids = list(product.variants.values_list("id", flat=True))

    response = post_action(
        admin_client,
        "admin:catalog_productvariant_changelist",
        "deactivate_selected_variants",
        variant_ids,
    )

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.is_active is True
    assert not ProductVariant.objects.filter(product=product, is_active=True).exists()
    logs = AuditLog.objects.filter(
        model="productvariant",
        metadata__admin_action="deactivate_selected_variants",
    )
    assert logs.count() == 2


def test_inventory_manager_cannot_run_product_price_action(
    client, inventory_manager, product_factory
):
    product = product_factory(
        name="Inventory Cannot Price",
        base_price="100.00",
        variants=[{"sku": "INV-NO-PRICE"}],
    )
    client.force_login(inventory_manager)

    response = post_action(
        client,
        "admin:catalog_product_changelist",
        "increase_selected_product_prices_10_percent",
        [product.id],
    )

    product.refresh_from_db()
    assert response.status_code != 200
    assert product.base_price == Decimal("100.00")
    assert AuditLog.objects.count() == 0
