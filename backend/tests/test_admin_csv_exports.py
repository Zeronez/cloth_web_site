import csv
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

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
        username="csv-admin",
        email="csv-admin@example.com",
        password="AdminPass!2026",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


def read_csv(response):
    content = response.content.decode("utf-8-sig")
    return list(csv.DictReader(StringIO(content)))


def post_export(client, url_name, action, object_ids):
    return client.post(
        reverse(url_name),
        {
            "action": action,
            "_selected_action": [str(object_id) for object_id in object_ids],
        },
    )


def create_order(user, product_factory, *, status=Order.Status.PAID, sku="CSV-ORDER"):
    product = product_factory(
        name=f"Report {sku}",
        base_price="40.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=status,
        **shipping_payload(shipping_city="=Moscow"),
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
    return order, variant


def create_payment(order, *, status=Payment.Status.SUCCEEDED):
    method = PaymentMethod.objects.create(
        code=f"csv-card-{order.id}",
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
        external_payment_id=f"pay-{order.id}",
    )


def test_order_admin_exports_selected_orders_csv(admin_client, user, product_factory):
    order, _variant = create_order(user, product_factory, sku="CSV-ORDER-1")
    create_payment(order)

    response = post_export(
        admin_client,
        "admin:orders_order_changelist",
        "export_orders_csv",
        [order.id],
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    rows = read_csv(response)
    assert list(rows[0].keys()) == [
        "order_id",
        "created_at",
        "customer_email",
        "status",
        "status_label",
        "total_amount",
        "shipping_city",
        "track_number",
        "payment_status",
    ]
    assert rows[0]["order_id"] == str(order.id)
    assert rows[0]["customer_email"] == "shopper@example.com"
    assert rows[0]["shipping_city"] == "'=Moscow"
    assert rows[0]["payment_status"] == Payment.Status.SUCCEEDED


def test_payment_admin_exports_selected_payments_csv(
    admin_client, user, product_factory
):
    order, _variant = create_order(user, product_factory, sku="CSV-PAY-1")
    payment = create_payment(order, status=Payment.Status.FAILED)

    response = post_export(
        admin_client,
        "admin:payments_payment_changelist",
        "export_payments_csv",
        [payment.id],
    )

    rows = read_csv(response)
    assert list(rows[0].keys()) == [
        "payment_id",
        "order_id",
        "customer_email",
        "method_code",
        "provider_code",
        "status",
        "amount",
        "currency",
        "external_payment_id",
        "created_at",
    ]
    assert rows[0]["payment_id"] == str(payment.id)
    assert rows[0]["status"] == Payment.Status.FAILED
    assert rows[0]["amount"] == "125.00"


def test_product_variant_admin_exports_sku_stock_csv(admin_client, product_factory):
    product = product_factory(
        name="=Danger Hoodie",
        base_price="80.00",
        variants=[{"sku": "CSV-SKU-1", "stock_quantity": 2}],
    )
    variant = product.variants.get()

    response = post_export(
        admin_client,
        "admin:catalog_productvariant_changelist",
        "export_sku_stock_csv",
        [variant.id],
    )

    rows = read_csv(response)
    assert list(rows[0].keys()) == [
        "sku",
        "product_name",
        "category",
        "size",
        "color",
        "stock_quantity",
        "low_stock",
        "is_active",
        "price",
    ]
    assert rows[0]["sku"] == "CSV-SKU-1"
    assert rows[0]["product_name"] == "'=Danger Hoodie"
    assert rows[0]["stock_quantity"] == "2"
    assert rows[0]["low_stock"] == "yes"


def test_user_admin_exports_minimal_customer_csv(admin_client):
    customer = get_user_model().objects.create_user(
        username="=danger-customer",
        email="customer@example.com",
        password="CustomerPass!2026",
        first_name="Formula",
        last_name="Tester",
        phone="+79990000000",
    )

    response = post_export(
        admin_client,
        "admin:users_user_changelist",
        "export_customers_csv",
        [customer.id],
    )

    rows = read_csv(response)
    assert list(rows[0].keys()) == [
        "customer_id",
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
        "is_active",
        "date_joined",
        "orders_count",
    ]
    assert rows[0]["username"] == "'=danger-customer"
    assert "password" not in rows[0]
    assert "is_superuser" not in rows[0]


def test_non_staff_user_cannot_export_admin_csv(client, user, product_factory):
    order, _variant = create_order(user, product_factory, sku="CSV-DENY-1")
    client.force_login(user)

    response = post_export(
        client,
        "admin:orders_order_changelist",
        "export_orders_csv",
        [order.id],
    )

    assert response.status_code == 302


def test_csv_safety_helper_escapes_formula_prefixes():
    from config.admin_exports import safe_csv_value

    assert safe_csv_value("=1+1") == "'=1+1"
    assert safe_csv_value("+1") == "'+1"
    assert safe_csv_value("-1") == "'-1"
    assert safe_csv_value("@SUM") == "'@SUM"
