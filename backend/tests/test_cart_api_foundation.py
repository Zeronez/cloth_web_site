import pytest

from cart.models import Cart, CartItem
from catalog.models import ProductVariant


pytestmark = pytest.mark.django_db


def assert_error_shape(response, *, status_code, code):
    assert response.status_code == status_code
    assert set(response.data) == {"error"}
    error = response.data["error"]
    assert error["status"] == status_code
    assert error["code"] == code
    assert isinstance(error["details"], dict)
    assert error["request_id"]
    assert error["correlation_id"]
    return error


def test_guest_cart_is_created_for_session_client(api_client):
    response = api_client.get("/api/cart/")

    assert response.status_code == 200
    assert response.data["items"] == []
    assert response.data["total_quantity"] == 0
    assert response.data["total_amount"] == "0.00"

    session_key = api_client.session.session_key
    assert session_key

    cart = Cart.objects.get(session_key=session_key)
    assert cart.user is None
    assert cart.items.count() == 0


def test_authenticated_cart_is_created_for_current_user(authenticated_client, user):
    response = authenticated_client.get("/api/cart/")

    assert response.status_code == 200
    assert response.data["items"] == []
    assert response.data["total_quantity"] == 0
    assert response.data["total_amount"] == "0.00"

    cart = Cart.objects.get(user=user)
    assert cart.session_key == ""
    assert cart.items.count() == 0


def test_cart_rejects_inactive_variant_on_add(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Inactive Variant Tee",
        variants=[
            {
                "sku": "INACTIVE-VARIANT-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
                "is_active": False,
            }
        ],
    )
    variant = product.variants.get()

    response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    error = assert_error_shape(response, status_code=400, code="validation_error")
    assert error["details"]["variant"] == [
        {"message": "This variant is not available.", "code": "invalid"}
    ]
    assert not CartItem.objects.filter(cart__user=user, variant=variant).exists()


def test_cart_rejects_variant_of_inactive_product_on_add(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Archived Product Tee",
        is_active=False,
        variants=[
            {
                "sku": "ARCHIVED-PRODUCT-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
            }
        ],
    )
    variant = product.variants.get()

    response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    error = assert_error_shape(response, status_code=400, code="validation_error")
    assert error["details"]["variant"] == [
        {"message": "This variant is not available.", "code": "invalid"}
    ]
    assert not CartItem.objects.filter(cart__user=user, variant=variant).exists()


def test_cart_rejects_quantity_above_stock_on_add(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Limited Stock Tee",
        variants=[
            {
                "sku": "LIMITED-STOCK-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 2,
            }
        ],
    )
    variant = product.variants.get()

    response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 3},
        format="json",
    )

    error = assert_error_shape(response, status_code=400, code="validation_error")
    assert error["details"]["quantity"] == [
        {
            "message": "Requested quantity exceeds available stock.",
            "code": "invalid",
        }
    ]
    assert not CartItem.objects.filter(cart__user=user, variant=variant).exists()


def test_cart_rejects_quantity_above_stock_on_update(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Update Limited Tee",
        variants=[
            {
                "sku": "UPDATE-LIMITED-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 3,
            }
        ],
    )
    variant = product.variants.get()

    add_response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_response.status_code == 201
    item_id = add_response.data["items"][0]["id"]

    response = authenticated_client.patch(
        f"/api/cart/items/{item_id}/",
        {"quantity": 4},
        format="json",
    )

    error = assert_error_shape(response, status_code=400, code="validation_error")
    assert error["details"]["quantity"] == [
        {
            "message": "Requested quantity exceeds available stock.",
            "code": "invalid",
        }
    ]
    assert CartItem.objects.get(cart__user=user, variant=variant).quantity == 1
