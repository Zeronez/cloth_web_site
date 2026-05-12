from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from catalog.admin import ProductAdmin, ProductVariantAdmin
from catalog.models import AnimeFranchise, Category, Product, ProductVariant
from delivery.models import DeliveryMethod, OrderDeliverySnapshot
from delivery.services import create_order_delivery_snapshot
from orders.admin import OrderAdmin, OrderItemAdmin, OrderSkuListFilter
from orders.models import Order, OrderItem
from payments.admin import PaymentAdmin, PaymentMethodAdmin
from payments.models import Payment, PaymentMethod
from favorites.models import FavoriteProduct
from users.models import Address
from users.admin import AnimeAttireUserAdmin


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+79990000000",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Admin filter street 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="filters-admin",
        email="filters-admin@example.com",
        password="AdminPass!2026",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


def changelist_result_ids(response):
    assert response.status_code == 200
    return [obj.id for obj in response.context["cl"].result_list]


def create_order(
    user,
    product_factory,
    *,
    sku,
    status=Order.Status.PAID,
    method_kind=DeliveryMethod.Kind.COURIER,
    method_code=None,
    provider_code="manual",
    tracking_status=OrderDeliverySnapshot.TrackingStatus.PENDING,
    city="Moscow",
):
    product = product_factory(
        name=f"Admin Filter {sku}",
        base_price="50.00",
        variants=[{"sku": sku, "stock_quantity": 5}],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("100.00"),
        status=status,
        **shipping_payload(shipping_city=city),
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
    method = DeliveryMethod.objects.create(
        code=method_code or f"delivery-{sku.lower()}",
        name=f"Delivery {sku}",
        kind=method_kind,
        price_amount=Decimal("300.00"),
    )
    snapshot = create_order_delivery_snapshot(
        order, method, shipping_payload(shipping_city=city)
    )
    snapshot.provider_code = provider_code
    snapshot.tracking_status = tracking_status
    snapshot.save(update_fields=["provider_code", "tracking_status"])
    return order


def create_payment(order, *, status=Payment.Status.SUCCEEDED, method_code="card"):
    method = PaymentMethod.objects.create(
        code=f"{method_code}-{order.id}",
        name=f"{method_code} payment",
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


def test_order_admin_declares_operational_filters():
    assert OrderSkuListFilter in OrderAdmin.list_filter
    assert "payments__status" in OrderAdmin.list_filter
    assert "delivery_snapshot__method_kind" in OrderAdmin.list_filter
    assert "shipping_city" in OrderAdmin.list_filter
    assert OrderAdmin.date_hierarchy == "created_at"
    assert OrderItemAdmin.date_hierarchy == "order__created_at"


def test_order_changelist_filters_by_status_without_losing_dashboard_context(
    admin_client, user, product_factory
):
    paid = create_order(
        user, product_factory, sku="ADMIN-FILTER-PAID", status=Order.Status.PAID
    )
    create_order(
        user,
        product_factory,
        sku="ADMIN-FILTER-PENDING",
        status=Order.Status.PENDING,
    )

    response = admin_client.get(
        reverse("admin:orders_order_changelist"),
        {"status__exact": Order.Status.PAID},
    )

    assert changelist_result_ids(response) == [paid.id]
    assert "fulfillment_summary" in response.context


def test_order_changelist_filters_by_exact_sku(admin_client, user, product_factory):
    matching = create_order(user, product_factory, sku="ADMIN-FILTER-SKU-A")
    create_order(user, product_factory, sku="ADMIN-FILTER-SKU-B")

    response = admin_client.get(
        reverse("admin:orders_order_changelist"),
        {"sku": "ADMIN-FILTER-SKU-A"},
    )

    assert changelist_result_ids(response) == [matching.id]


def test_order_changelist_filters_by_delivery_method_and_tracking_status(
    admin_client, user, product_factory
):
    matching = create_order(
        user,
        product_factory,
        sku="ADMIN-DELIVERY-A",
        method_kind=DeliveryMethod.Kind.PICKUP,
        method_code="pickup-admin",
        provider_code="manual",
        tracking_status=OrderDeliverySnapshot.TrackingStatus.FAILED,
    )
    create_order(
        user,
        product_factory,
        sku="ADMIN-DELIVERY-B",
        method_kind=DeliveryMethod.Kind.COURIER,
        method_code="courier-admin",
        provider_code="cdek",
        tracking_status=OrderDeliverySnapshot.TrackingStatus.CREATED,
    )

    response = admin_client.get(
        reverse("admin:orders_order_changelist"),
        {
            "delivery_snapshot__method_code__exact": "pickup-admin",
            "delivery_snapshot__method_kind__exact": DeliveryMethod.Kind.PICKUP,
            "delivery_snapshot__tracking_status__exact": OrderDeliverySnapshot.TrackingStatus.FAILED,
        },
    )

    assert changelist_result_ids(response) == [matching.id]


def test_order_changelist_filters_by_provider_country_priority_and_restock_state(
    admin_client, user, product_factory
):
    matching = create_order(
        user,
        product_factory,
        sku="ADMIN-OPS-A",
        provider_code="cdek",
        city="Kazan",
    )
    matching.priority = Order.Priority.URGENT
    matching.stock_restored_at = "2026-05-12T10:00:00Z"
    matching.shipping_country = "RU"
    matching.save(
        update_fields=[
            "priority",
            "stock_restored_at",
            "shipping_country",
            "updated_at",
        ]
    )
    create_order(
        user,
        product_factory,
        sku="ADMIN-OPS-B",
        provider_code="boxberry",
        city="Almaty",
    )

    response = admin_client.get(
        reverse("admin:orders_order_changelist"),
        {
            "delivery_snapshot__provider_code__exact": "cdek",
            "shipping_country__exact": "RU",
            "priority__exact": Order.Priority.URGENT,
            "stock_restored_at__isnull": "False",
        },
    )

    assert changelist_result_ids(response) == [matching.id]


def test_product_changelist_filters_by_category_and_franchise(
    admin_client, product_factory
):
    category_a = Category.objects.create(name="Admin Category A")
    category_b = Category.objects.create(name="Admin Category B")
    franchise_x = AnimeFranchise.objects.create(name="Admin Franchise X")
    franchise_y = AnimeFranchise.objects.create(name="Admin Franchise Y")
    matching = product_factory(
        name="Admin Matrix Match",
        category=category_a,
        franchise=franchise_x,
        variants=[{"sku": "ADMIN-MATRIX-1"}],
    )
    product_factory(
        name="Admin Matrix Wrong Category",
        category=category_b,
        franchise=franchise_x,
        variants=[{"sku": "ADMIN-MATRIX-2"}],
    )
    product_factory(
        name="Admin Matrix Wrong Franchise",
        category=category_a,
        franchise=franchise_y,
        variants=[{"sku": "ADMIN-MATRIX-3"}],
    )

    response = admin_client.get(
        reverse("admin:catalog_product_changelist"),
        {
            "category__id__exact": str(category_a.id),
            "franchise__id__exact": str(franchise_x.id),
        },
    )

    assert changelist_result_ids(response) == [matching.id]


def test_product_changelist_filters_by_archived_and_active_flags(
    admin_client, product_factory
):
    archived = product_factory(
        name="Archived Admin Drop",
        variants=[{"sku": "ADMIN-ARCHIVE-1"}],
    )
    archived.archive()
    active = product_factory(
        name="Live Admin Drop",
        variants=[{"sku": "ADMIN-ARCHIVE-2"}],
    )

    archived_response = admin_client.get(
        reverse("admin:catalog_product_changelist"),
        {"archived_at__isnull": "False"},
    )
    active_response = admin_client.get(
        reverse("admin:catalog_product_changelist"),
        {"is_active__exact": "1"},
    )

    assert changelist_result_ids(archived_response) == [archived.id]
    assert active.id in changelist_result_ids(active_response)
    assert archived.id not in changelist_result_ids(active_response)


def test_product_search_by_variant_sku_returns_product_once(
    admin_client, product_factory
):
    matching = product_factory(
        name="Admin SKU Family",
        variants=[
            {"sku": "ADMIN-FAMILY-RED", "color": "Red"},
            {"sku": "ADMIN-FAMILY-BLUE", "color": "Blue"},
        ],
    )
    product_factory(name="Other SKU Family", variants=[{"sku": "ADMIN-OTHER"}])

    response = admin_client.get(
        reverse("admin:catalog_product_changelist"), {"q": "ADMIN-FAMILY"}
    )

    assert changelist_result_ids(response) == [matching.id]


def test_product_variant_admin_declares_franchise_and_date_filters():
    assert "product__franchise" in ProductVariantAdmin.list_filter
    assert "created_at" in ProductVariantAdmin.list_filter
    assert ProductVariantAdmin.date_hierarchy == "created_at"
    assert ProductAdmin.date_hierarchy == "created_at"


def test_product_variant_changelist_filters_by_category_active_and_low_stock(
    admin_client, product_factory
):
    category = Category.objects.create(name="Admin Variant Category")
    matching_product = product_factory(
        name="Admin Variant Match",
        category=category,
        variants=[
            {
                "sku": "ADMIN-VARIANT-LOW",
                "stock_quantity": 2,
                "is_active": True,
            }
        ],
    )
    product_factory(
        name="Admin Variant Wrong Stock",
        category=category,
        variants=[{"sku": "ADMIN-VARIANT-NORMAL", "stock_quantity": 50}],
    )
    matching = ProductVariant.objects.get(product=matching_product)

    response = admin_client.get(
        reverse("admin:catalog_productvariant_changelist"),
        {
            "product__category__id__exact": str(category.id),
            "is_active__exact": "1",
            "low_stock": "yes",
        },
    )

    assert changelist_result_ids(response) == [matching.id]


def test_payment_changelist_filters_by_status_and_method(
    admin_client, user, product_factory
):
    matching_order = create_order(user, product_factory, sku="ADMIN-PAY-FILTER-A")
    other_order = create_order(user, product_factory, sku="ADMIN-PAY-FILTER-B")
    matching = create_payment(
        matching_order, status=Payment.Status.FAILED, method_code="card-admin"
    )
    create_payment(
        other_order, status=Payment.Status.SUCCEEDED, method_code="sbp-admin"
    )

    response = admin_client.get(
        reverse("admin:payments_payment_changelist"),
        {
            "status__exact": Payment.Status.FAILED,
            "method_code": matching.method_code,
        },
    )

    assert changelist_result_ids(response) == [matching.id]
    assert "method_code" in PaymentAdmin.list_filter
    assert PaymentAdmin.date_hierarchy == "created_at"


def test_payment_method_changelist_filters_by_provider_and_session_mode(
    admin_client,
):
    matching = PaymentMethod.objects.create(
        code="provider-filter-card",
        name="Provider Filter Card",
        provider_code="yookassa",
        session_mode=PaymentMethod.SessionMode.REDIRECT,
        currency="RUB",
    )
    PaymentMethod.objects.create(
        code="provider-filter-sbp",
        name="Provider Filter SBP",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
        currency="RUB",
    )

    response = admin_client.get(
        reverse("admin:payments_paymentmethod_changelist"),
        {
            "provider_code__exact": "yookassa",
            "session_mode__exact": PaymentMethod.SessionMode.REDIRECT,
        },
    )

    assert changelist_result_ids(response) == [matching.id]
    assert PaymentMethodAdmin.date_hierarchy == "created_at"


def test_user_admin_declares_customer_lifecycle_filters():
    assert "date_joined" in AnimeAttireUserAdmin.list_filter
    assert "last_login" in AnimeAttireUserAdmin.list_filter
    assert AnimeAttireUserAdmin.date_hierarchy == "date_joined"


def test_real_admin_query_paths_are_backed_by_index_contracts():
    product_index_fields = {tuple(index.fields) for index in Product._meta.indexes}
    variant_index_fields = {
        tuple(index.fields) for index in ProductVariant._meta.indexes
    }
    order_index_fields = {tuple(index.fields) for index in Order._meta.indexes}
    payment_method_index_fields = {
        tuple(index.fields) for index in PaymentMethod._meta.indexes
    }
    payment_index_fields = {tuple(index.fields) for index in Payment._meta.indexes}
    snapshot_index_fields = {
        tuple(index.fields) for index in OrderDeliverySnapshot._meta.indexes
    }
    favorite_index_fields = {
        tuple(index.fields) for index in FavoriteProduct._meta.indexes
    }
    address_index_fields = {tuple(index.fields) for index in Address._meta.indexes}

    assert ("archived_at",) in product_index_fields
    assert ("is_active", "is_featured") in product_index_fields
    assert (
        "is_active",
        "archived_at",
        "is_featured",
        "created_at",
    ) in product_index_fields
    assert ("sku",) in variant_index_fields
    assert ("is_active", "stock_quantity") in variant_index_fields
    assert ("priority",) in order_index_fields
    assert ("stock_restored_at",) in order_index_fields
    assert ("status", "created_at") in order_index_fields
    assert ("user", "created_at") in order_index_fields
    assert ("shipping_country", "shipping_city") in order_index_fields
    assert ("provider_code", "session_mode") in payment_method_index_fields
    assert ("user", "created_at") in payment_index_fields
    assert ("order", "provider_code", "external_payment_id") in payment_index_fields
    assert ("provider_code", "status") in payment_index_fields
    assert ("method_code",) in payment_index_fields
    assert ("status", "created_at") in payment_index_fields
    assert ("session_expires_at",) in payment_index_fields
    assert ("method_kind",) in snapshot_index_fields
    assert ("provider_code", "tracking_status") in snapshot_index_fields
    assert ("user", "created_at") in favorite_index_fields
    assert ("user", "is_default", "created_at") in address_index_fields
