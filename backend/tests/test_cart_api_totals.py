from decimal import Decimal

import pytest

from cart.models import Cart
from catalog.models import ProductVariant


pytestmark = pytest.mark.django_db


def test_cart_api_returns_matching_quantity_and_amount_totals(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Storm Pilot Tee",
        base_price="29.90",
        variants=[
            {
                "sku": "STORM-TEE-BLK-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
            }
        ],
    )
    variant = product.variants.get()

    add_response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 2},
        format="json",
    )

    assert add_response.status_code == 201
    assert add_response.data["total_quantity"] == 2
    assert add_response.data["total_amount"] == "59.80"
    assert add_response.data["subtotal_amount"] == "59.80"

    item_id = add_response.data["items"][0]["id"]

    cart_response = authenticated_client.get("/api/cart/")

    assert cart_response.status_code == 200
    assert cart_response.data["total_quantity"] == 2
    assert cart_response.data["total_amount"] == "59.80"
    assert cart_response.data["subtotal_amount"] == "59.80"

    patch_response = authenticated_client.patch(
        f"/api/cart/items/{item_id}/",
        {"quantity": 3},
        format="json",
    )

    assert patch_response.status_code == 200
    assert patch_response.data["total_quantity"] == 3
    assert patch_response.data["total_amount"] == "89.70"
    assert patch_response.data["subtotal_amount"] == "89.70"

    cart = Cart.objects.get(user=user)
    assert cart.total_quantity == 3
    assert cart.total_amount == Decimal("89.70")
