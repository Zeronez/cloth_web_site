from decimal import Decimal

import pytest

from pricing.models import Coupon
from delivery.models import DeliveryMethod


pytestmark = pytest.mark.django_db


def test_cart_apply_coupon_percent_updates_totals(authenticated_client, product_factory):
    product = product_factory(
        name="Coupon Tee",
        base_price="100.00",
        variants=[
            {
                "sku": "COUPON-TEE-M",
                "size": "M",
                "color": "Black",
                "stock_quantity": 10,
                "price_delta": "0.00",
            }
        ],
    )
    variant = product.variants.get()
    Coupon.objects.create(
        code="TENOFF",
        kind=Coupon.Kind.PERCENT,
        percent=10,
        currency="RUB",
        min_cart_amount=Decimal("0.00"),
        per_user_limit=10,
        is_active=True,
    )

    add_response = authenticated_client.post(
        "/api/v1/cart/items/",
        {"variant_id": variant.id, "quantity": 2},
        format="json",
    )
    assert add_response.status_code == 201

    apply_response = authenticated_client.post(
        "/api/v1/cart/coupon/",
        {"coupon_code": "TENOFF"},
        format="json",
    )
    assert apply_response.status_code == 200
    assert apply_response.data["coupon_code"] == "TENOFF"
    assert apply_response.data["items_subtotal_amount"] == "200.00"
    assert apply_response.data["discount_amount"] == "20.00"
    assert apply_response.data["total_amount"] == "180.00"


def test_cart_quote_applies_free_shipping_coupon(authenticated_client, product_factory):
    product = product_factory(
        name="FreeShip Tee",
        base_price="100.00",
        variants=[
            {
                "sku": "FREESHIP-TEE-M",
                "size": "M",
                "color": "Black",
                "stock_quantity": 10,
                "price_delta": "0.00",
            }
        ],
    )
    variant = product.variants.get()
    Coupon.objects.create(
        code="SHIPFREE",
        kind=Coupon.Kind.FREE_SHIPPING,
        currency="RUB",
        min_cart_amount=Decimal("0.00"),
        per_user_limit=10,
        is_active=True,
    )

    add_response = authenticated_client.post(
        "/api/v1/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_response.status_code == 201

    DeliveryMethod.objects.create(
        code="courier_moscow",
        name="Courier Moscow",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        currency="RUB",
        is_active=True,
        sort_order=10,
    )

    quote_response = authenticated_client.post(
        "/api/v1/cart/quote/",
        {
            "delivery_method_code": "courier_moscow",
            "shipping_country": "RU",
            "shipping_city": "Moscow",
            "shipping_postal_code": "101000",
            "coupon_code": "SHIPFREE",
        },
        format="json",
    )
    assert quote_response.status_code == 200
    assert quote_response.data["coupon_code"] == "SHIPFREE"
    assert quote_response.data["delivery_amount"] == "0.00"
