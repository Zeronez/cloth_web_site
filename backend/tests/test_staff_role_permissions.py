from decimal import Decimal
from io import StringIO

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse

from catalog.admin import ProductAdmin
from catalog.models import Product
from orders.admin import OrderAdmin
from orders.models import Order
from payments.admin import PaymentAdmin, PaymentMethodAdmin
from payments.models import Payment, PaymentMethod
from support.models import ContactRequest
from users.staff_roles import (
    ROLE_ACCOUNTANT,
    ROLE_ORDER_MANAGER,
    ROLE_SUPPORT_AGENT,
    ROLE_WAREHOUSE_OPERATOR,
)


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
def request_factory():
    return RequestFactory()


@pytest.fixture
def sync_roles(db):
    call_command("sync_staff_roles")


@pytest.fixture
def staff_user_factory(db, sync_roles):
    def create_user(*roles):
        user = get_user_model().objects.create_user(
            username="-".join(roles) or "staffer",
            email=f"{'-'.join(roles) or 'staffer'}@example.com",
            password="StaffPass!2026",
            is_staff=True,
        )
        for role in roles:
            user.groups.add(Group.objects.get(name=role))
        return user

    return create_user


def test_sync_staff_roles_command_creates_groups_and_permissions(sync_roles):
    output = StringIO()
    call_command("sync_staff_roles", stdout=output)

    assert Group.objects.filter(name=ROLE_WAREHOUSE_OPERATOR).exists()
    assert Group.objects.filter(name=ROLE_SUPPORT_AGENT).exists()
    assert Group.objects.filter(name=ROLE_ORDER_MANAGER).exists()
    support_group = Group.objects.get(name=ROLE_SUPPORT_AGENT)
    permission_codes = set(
        support_group.permissions.values_list("content_type__app_label", "codename")
    )
    assert ("support", "change_contactrequest") in permission_codes
    assert ("orders", "view_order") in permission_codes
    assert "Synced staff roles:" in output.getvalue()


def test_support_agent_order_admin_is_note_only(
    request_factory, staff_user_factory, user
):
    support_user = staff_user_factory(ROLE_SUPPORT_AGENT)
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    request = request_factory.get("/admin/orders/order/")
    request.user = support_user
    admin_instance: OrderAdmin = admin.site._registry[Order]

    actions = admin_instance.get_actions(request)
    readonly = set(admin_instance.get_readonly_fields(request, order))

    assert actions == {}
    assert "internal_note" not in readonly
    assert "priority" not in readonly
    assert "status" in readonly
    assert "assignee" in readonly


def test_warehouse_operator_actions_are_limited_and_catalog_hidden(
    request_factory, staff_user_factory
):
    warehouse_user = staff_user_factory(ROLE_WAREHOUSE_OPERATOR)
    request = request_factory.get("/admin/orders/order/")
    request.user = warehouse_user

    order_admin: OrderAdmin = admin.site._registry[Order]
    catalog_admin: ProductAdmin = admin.site._registry[Product]
    action_names = set(order_admin.get_actions(request).keys())

    assert {
        "mark_picking",
        "mark_packed",
        "mark_shipped",
        "confirm_return_received",
    } <= action_names
    assert "mark_cancelled" not in action_names
    assert "mark_returned" not in action_names
    assert "create_shipment" not in action_names
    assert "refresh_tracking" not in action_names
    assert catalog_admin.has_module_permission(request) is False


def test_payment_admin_is_read_only_for_accountant(request_factory, staff_user_factory):
    accountant_user = staff_user_factory(ROLE_ACCOUNTANT)
    request = request_factory.get("/admin/payments/payment/")
    request.user = accountant_user

    payment_admin: PaymentAdmin = admin.site._registry[Payment]
    payment_method_admin: PaymentMethodAdmin = admin.site._registry[PaymentMethod]
    readonly = set(payment_admin.get_readonly_fields(request))

    assert payment_admin.has_module_permission(request) is True
    assert payment_method_admin.has_module_permission(request) is True
    assert {"status", "amount", "external_payment_id", "idempotency_key"} <= readonly
    assert payment_admin.has_add_permission(request) is False
    assert payment_admin.has_delete_permission(request) is False


def test_superuser_cannot_delete_products_or_orders_via_admin(request_factory):
    superuser = get_user_model().objects.create_superuser(
        username="delete-blocked-admin",
        email="delete-blocked-admin@example.com",
        password="AdminPass!2026",
    )
    request = request_factory.get("/admin/")
    request.user = superuser

    product_admin: ProductAdmin = admin.site._registry[Product]
    order_admin: OrderAdmin = admin.site._registry[Order]

    assert product_admin.has_delete_permission(request) is False
    assert order_admin.has_delete_permission(request) is False


def test_support_agent_admin_access_is_scoped(
    client, staff_user_factory, user, product_factory
):
    support_user = staff_user_factory(ROLE_SUPPORT_AGENT)
    client.force_login(support_user)
    product = product_factory(name="Scoped Tee")
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        **shipping_payload(),
    )
    ContactRequest.objects.create(
        name="QA Shopper",
        email="shopper@example.com",
        topic=ContactRequest.Topic.ORDER,
        order_number=str(order.id),
        message="Где мой заказ?",
    )

    orders_response = client.get(reverse("admin:orders_order_changelist"))
    support_response = client.get(reverse("admin:support_contactrequest_changelist"))
    catalog_response = client.get(reverse("admin:catalog_product_changelist"))

    assert orders_response.status_code == 200
    assert support_response.status_code == 200
    assert catalog_response.status_code != 200
    assert product.name not in catalog_response.content.decode("utf-8", errors="ignore")
