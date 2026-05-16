from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import RequestFactory
from django.urls import reverse

from audit.models import AuditLog
from audit.services import log_admin_event, model_changes, model_snapshot
from catalog.admin import ProductAdmin
from catalog.models import Category, InventoryAdjustment, Product
from delivery.models import DeliveryMethod
from delivery.services import create_order_delivery_snapshot
from orders.models import Order, OrderItem
from payments.models import Payment


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+79990000000",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Audit street 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="audit-admin",
        email="audit-admin@example.com",
        password="AdminPass!2026",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


def make_request(admin_user, path="/admin/audit-test/"):
    request = RequestFactory().post(
        path,
        HTTP_USER_AGENT="pytest-admin",
        REMOTE_ADDR="127.0.0.1",
    )
    request.user = admin_user
    return request


def create_order(user, product_factory, *, status=Order.Status.PAID, sku="AUDIT-ORDER"):
    product = product_factory(
        name=f"Audit {sku}",
        base_price="40.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("80.00"),
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
    method = DeliveryMethod.objects.create(
        code=f"audit-delivery-{sku.lower()}",
        name="Audit delivery",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("300.00"),
    )
    create_order_delivery_snapshot(order, method, shipping_payload())
    return order


def test_audited_admin_product_change_creates_audit_log(admin_user, product_factory):
    product = product_factory(
        name="Audit Hoodie",
        base_price="80.00",
        variants=[{"sku": "AUDIT-HOODIE-M"}],
    )
    old_product = Product.objects.get(pk=product.pk)
    product.base_price = Decimal("95.00")
    product.is_active = False
    form = type("AuditForm", (), {"changed_data": ["base_price", "is_active"]})()
    request = make_request(
        admin_user, reverse("admin:catalog_product_change", args=[product.id])
    )

    ProductAdmin(Product, admin.site).save_model(request, product, form, change=True)

    log = AuditLog.objects.get(model="product", object_id=str(product.id))
    assert log.actor == admin_user
    assert log.action == AuditLog.Action.CHANGE
    assert log.app_label == "catalog"
    assert log.object_repr
    assert log.changes == {
        "base_price": {"old": "80.00", "new": "95.00"},
        "is_active": {"old": True, "new": False},
    }
    assert log.request_path.endswith(f"/catalog/product/{product.id}/change/")
    assert old_product.base_price == Decimal("80.00")


def test_order_admin_status_action_creates_audit_log(
    admin_client, user, product_factory
):
    order = create_order(
        user, product_factory, status=Order.Status.PAID, sku="AUDIT-PICKING"
    )

    response = admin_client.post(
        reverse("admin:orders_order_changelist"),
        {
            "action": "mark_picking",
            "_selected_action": [str(order.id)],
        },
        follow=True,
    )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PICKING
    log = AuditLog.objects.get(model="order", object_id=str(order.id))
    assert log.action == AuditLog.Action.ADMIN_ACTION
    assert log.metadata["admin_action"] == "transition_order_status"
    assert log.changes["status"] == {
        "old": Order.Status.PAID,
        "new": Order.Status.PICKING,
    }


def test_inventory_adjustment_admin_creates_audit_log(
    admin_client, admin_user, product_factory
):
    product = product_factory(
        name="Audit Stock Tee",
        variants=[{"sku": "AUDIT-STOCK-M", "stock_quantity": 5}],
    )
    variant = product.variants.get()

    response = admin_client.post(
        reverse("admin:catalog_inventoryadjustment_add"),
        {
            "variant": variant.id,
            "reason": InventoryAdjustment.Reason.RESTOCK,
            "delta": 3,
            "note": "Internal supplier note",
        },
        follow=True,
    )

    assert response.status_code == 200
    adjustment = InventoryAdjustment.objects.get(variant=variant)
    log = AuditLog.objects.get(
        model="inventoryadjustment", object_id=str(adjustment.id)
    )
    assert adjustment.performed_by == admin_user
    assert log.actor == admin_user
    assert log.metadata["sku"] == "AUDIT-STOCK-M"
    assert log.snapshot["delta"] == 3
    assert log.snapshot["new_quantity"] == 8
    assert log.snapshot["note"] == "[redacted]"


def test_admin_delete_creates_audit_log_with_snapshot(admin_client):
    category = Category.objects.create(name="Audit Delete Category")

    response = admin_client.post(
        reverse("admin:catalog_category_delete", args=[category.id]),
        {"post": "yes"},
        follow=True,
    )

    assert response.status_code == 200
    assert not Category.objects.filter(id=category.id).exists()
    log = AuditLog.objects.get(model="category", object_id=str(category.id))
    assert log.action == AuditLog.Action.DELETE
    assert log.object_repr == "Audit Delete Category"
    assert log.snapshot["name"] == "Audit Delete Category"


def test_audit_log_service_redacts_sensitive_changes(user):
    old_order = Order(
        user=user,
        total_amount=Decimal("10.00"),
        **shipping_payload(shipping_phone="+79990000000"),
    )
    new_order = Order(
        user=user,
        total_amount=Decimal("10.00"),
        **shipping_payload(shipping_phone="+79991111111"),
    )

    changes = model_changes(old_order, new_order, ["shipping_phone", "shipping_city"])

    assert changes["shipping_phone"] == {
        "old": "[redacted]",
        "new": "[redacted]",
    }
    assert "shipping_city" not in changes


def test_audit_log_is_append_only(admin_user, product_factory):
    product = product_factory(name="Audit Append Only", variants=[{"sku": "AUDIT-APP"}])
    log = log_admin_event(
        actor=admin_user,
        action=AuditLog.Action.CHANGE,
        obj=product,
        changes={"is_active": {"old": True, "new": False}},
    )

    log.metadata = {"tamper": True}
    with pytest.raises(ValidationError):
        log.save()

    with pytest.raises(ValidationError):
        log.delete()


def test_audit_log_rolls_back_with_transaction(admin_user, product_factory):
    product = product_factory(name="Audit Rollback", variants=[{"sku": "AUDIT-ROLL"}])

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            log_admin_event(
                actor=admin_user,
                action=AuditLog.Action.CHANGE,
                obj=product,
                changes={"is_active": {"old": True, "new": False}},
            )
            raise RuntimeError("rollback")

    assert AuditLog.objects.count() == 0


def test_payment_export_creates_audit_without_exporting_pii_to_metadata(
    admin_client, user, product_factory
):
    order = create_order(user, product_factory, sku="AUDIT-PAYMENT")
    payment = Payment.objects.create(
        order=order,
        user=user,
        method_code="card",
        provider_code="placeholder",
        amount=order.total_amount,
        currency="RUB",
        status=Payment.Status.FAILED,
    )

    response = admin_client.post(
        reverse("admin:payments_payment_changelist"),
        {
            "action": "export_payments_csv",
            "_selected_action": [str(payment.id)],
        },
    )

    assert response.status_code == 200
    log = AuditLog.objects.get(model="payment", object_id=str(payment.id))
    assert log.metadata == {
        "admin_action": "export_payments_csv",
        "selected_count": 1,
    }
    assert user.email not in str(log.metadata)


def test_audit_log_redacts_sensitive_metadata_and_object_repr(admin_user, user):
    address = user.addresses.create(
        label="Home",
        recipient_name="QA Shopper",
        phone="+79990001122",
        country="RU",
        city="Moscow",
        postal_code="101000",
        line1="Hidden street 1",
        line2="Apt 5",
        is_default=True,
    )

    log = log_admin_event(
        actor=admin_user,
        action=AuditLog.Action.ADMIN_ACTION,
        obj=address,
        metadata={
            "email": user.email,
            "shipping_phone": "+79990001122",
            "safe_flag": "ok",
        },
        snapshot=model_snapshot(address),
    )

    assert log.object_repr.startswith("Address #")
    assert log.metadata["email"] == "[redacted]"
    assert log.metadata["shipping_phone"] == "[redacted]"
    assert log.metadata["safe_flag"] == "ok"
    assert log.snapshot["recipient_name"] == "[redacted]"
    assert log.snapshot["line1"] == "[redacted]"
