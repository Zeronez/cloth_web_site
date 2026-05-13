from decimal import Decimal

import pytest

from delivery.models import DeliveryMethod
from orders.models import Order


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "11 Test Avenue",
        "shipping_line2": "Apt 5",
    }
    payload.update(overrides)
    return payload


def test_delivery_methods_api_uses_real_address_fixture_for_availability(
    api_client, settings
):
    DeliveryMethod.objects.create(
        code="courier-msk",
        name="Courier Moscow",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        sort_order=10,
    )
    DeliveryMethod.objects.create(
        code="pickup-cdek",
        name="Pickup CDEK",
        kind=DeliveryMethod.Kind.PICKUP,
        price_amount=Decimal("0.00"),
        sort_order=20,
    )
    DeliveryMethod.objects.create(
        code="post-ru",
        name="Russian Post",
        kind=DeliveryMethod.Kind.POST,
        price_amount=Decimal("250.00"),
        sort_order=30,
    )
    settings.DELIVERY_METHOD_AVAILABILITY_OVERRIDES = {
        "RU|moscow|101000": {
            "available_methods": ["courier-msk", "pickup-cdek"],
            "price_overrides": {
                "courier-msk": "490.00",
                "pickup-cdek": "50.00",
            },
        }
    }

    response = api_client.get(
        "/api/delivery-methods/",
        {"country": "RU", "city": "Moscow", "postal_code": "101000"},
    )

    assert response.status_code == 200
    assert [item["code"] for item in response.data["results"]] == [
        "courier-msk",
        "pickup-cdek",
    ]
    assert str(response.data["results"][0]["price_amount"]) == "490.00"
    assert str(response.data["results"][1]["price_amount"]) == "50.00"


def test_checkout_uses_delivery_fixture_price_for_real_address(
    authenticated_client, user, product_factory, settings
):
    product = product_factory(
        name="Fixture Delivery Tee",
        base_price="40.00",
        variants=[{"sku": "FIXTURE-DELIVERY-TEE", "stock_quantity": 2}],
    )
    variant = product.variants.get()
    DeliveryMethod.objects.create(
        code="courier-msk",
        name="Courier Moscow",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        sort_order=10,
    )
    DeliveryMethod.objects.create(
        code="pickup-cdek",
        name="Pickup CDEK",
        kind=DeliveryMethod.Kind.PICKUP,
        price_amount=Decimal("0.00"),
        sort_order=20,
    )
    settings.DELIVERY_METHOD_AVAILABILITY_OVERRIDES = {
        "RU|moscow|101000": {
            "available_methods": ["courier-msk", "pickup-cdek"],
            "price_overrides": {"courier-msk": "490.00"},
        }
    }
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 2},
        format="json",
    )

    response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(delivery_method_code="courier-msk"),
        format="json",
    )

    assert response.status_code == 201
    assert response.data["delivery"]["method_code"] == "courier-msk"
    assert response.data["delivery"]["price_amount"] == "490.00"
    assert response.data["total_amount"] == "570.00"
    order = Order.objects.get(user=user)
    assert order.total_amount == Decimal("570.00")
    assert order.delivery_snapshot.price_amount == Decimal("490.00")


def test_checkout_rejects_delivery_method_unavailable_for_address(
    authenticated_client, product_factory, settings
):
    product = product_factory(
        name="Fixture Delivery Reject Tee",
        base_price="40.00",
        variants=[{"sku": "FIXTURE-DELIVERY-REJECT-TEE", "stock_quantity": 1}],
    )
    variant = product.variants.get()
    DeliveryMethod.objects.create(
        code="courier-msk",
        name="Courier Moscow",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        sort_order=10,
    )
    DeliveryMethod.objects.create(
        code="post-ru",
        name="Russian Post",
        kind=DeliveryMethod.Kind.POST,
        price_amount=Decimal("250.00"),
        sort_order=30,
    )
    settings.DELIVERY_METHOD_AVAILABILITY_OVERRIDES = {
        "RU|moscow|101000": {
            "available_methods": ["courier-msk"],
            "price_overrides": {"courier-msk": "490.00"},
        }
    }
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(delivery_method_code="post-ru"),
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert (
        response.data["error"]["details"]["delivery_method_code"][0]["code"]
        == "delivery_method_unavailable"
    )


def test_pickup_point_search_returns_provider_format_points(api_client, settings):
    DeliveryMethod.objects.create(
        code="pickup-cdek",
        name="Pickup CDEK",
        kind=DeliveryMethod.Kind.PICKUP,
        price_amount=Decimal("0.00"),
        sort_order=20,
    )
    settings.DELIVERY_METHOD_AVAILABILITY_OVERRIDES = {
        "RU|moscow|101000": {"available_methods": ["pickup-cdek"]}
    }
    settings.DELIVERY_PICKUP_POINT_OVERRIDES = {
        "RU|moscow|101000": {
            "pickup-cdek": [
                {
                    "provider": "cdek",
                    "code": "CDEK-101",
                    "name": "CDEK Тверская",
                    "city": "Moscow",
                    "address": "Tverskaya 10",
                    "postal_code": "101000",
                    "latitude": "55.765200",
                    "longitude": "37.605100",
                    "work_time": "10:00-22:00",
                    "phone": "+74951234567",
                    "payment_cash": True,
                    "payment_card": True,
                    "fitting_room": True,
                },
                {
                    "provider": "cdek",
                    "code": "CDEK-102",
                    "name": "CDEK Арбат",
                    "city": "Moscow",
                    "address": "Arbat 21",
                    "postal_code": "101000",
                    "latitude": "55.752200",
                    "longitude": "37.592400",
                    "work_time": "09:00-21:00",
                    "phone": "+74957654321",
                    "payment_cash": True,
                    "payment_card": False,
                    "fitting_room": False,
                },
            ]
        }
    }

    response = api_client.get(
        "/api/delivery-methods/pickup-points/",
        {
            "method_code": "pickup-cdek",
            "country": "RU",
            "city": "Moscow",
            "postal_code": "101000",
            "query": "Твер",
        },
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    point = response.data["results"][0]
    assert point["provider"] == "cdek"
    assert point["code"] == "CDEK-101"
    assert point["name"] == "CDEK Тверская"
    assert point["address"] == "Tverskaya 10"
    assert str(point["latitude"]) == "55.765200"
    assert str(point["longitude"]) == "37.605100"
    assert point["payment_cash"] is True
    assert point["payment_card"] is True
    assert point["fitting_room"] is True


def test_pickup_point_search_rejects_non_pickup_method(api_client, settings):
    DeliveryMethod.objects.create(
        code="courier-msk",
        name="Courier Moscow",
        kind=DeliveryMethod.Kind.COURIER,
        price_amount=Decimal("350.00"),
        sort_order=10,
    )
    settings.DELIVERY_METHOD_AVAILABILITY_OVERRIDES = {
        "RU|moscow|101000": {"available_methods": ["courier-msk"]}
    }

    response = api_client.get(
        "/api/delivery-methods/pickup-points/",
        {
            "method_code": "courier-msk",
            "country": "RU",
            "city": "Moscow",
            "postal_code": "101000",
        },
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert (
        response.data["error"]["details"]["delivery_method_code"][0]["code"]
        == "pickup_method_required"
    )
