from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem
from catalog.models import AnimeFranchise, Category, ProductVariant
from favorites.models import FavoriteProduct
from orders.models import Order, OrderItem
from users.models import Address


pytestmark = pytest.mark.django_db


def paginated_items(response):
    payload = response.data
    if isinstance(payload, dict) and "results" in payload:
        return payload["results"]
    return payload


def address_payload(**overrides):
    payload = {
        "label": "Home",
        "recipient_name": "QA Shopper",
        "phone": "+15551234567",
        "country": "US",
        "city": "New York",
        "postal_code": "10001",
        "line1": "11 Test Avenue",
        "line2": "Apt 5",
        "is_default": True,
    }
    payload.update(overrides)
    return payload


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "US",
        "shipping_city": "New York",
        "shipping_postal_code": "10001",
        "shipping_line1": "11 Test Avenue",
        "shipping_line2": "Apt 5",
    }
    payload.update(overrides)
    return payload


def cart_item_id(cart_response, variant):
    for item in cart_response.data["items"]:
        if item["variant"]["id"] == variant.id:
            return item["id"]
    raise AssertionError(f"Variant {variant.id} was not returned in cart response.")


def test_user_can_register_login_and_refresh_jwt(api_client):
    registration = {
        "username": "new-shopper",
        "email": "new-shopper@example.com",
        "password": "GhibliMerch!2026",
        "first_name": "New",
        "last_name": "Shopper",
        "phone": "+15550001111",
    }

    register_response = api_client.post(
        "/api/auth/register/", registration, format="json"
    )

    assert register_response.status_code == 201
    assert register_response.data["username"] == "new-shopper"
    assert "password" not in register_response.data

    user = get_user_model().objects.get(username="new-shopper")
    assert user.email == "new-shopper@example.com"
    assert user.check_password("GhibliMerch!2026")

    login_response = api_client.post(
        "/api/auth/token/",
        {"username": "new-shopper", "password": "GhibliMerch!2026"},
        format="json",
    )

    assert login_response.status_code == 200
    assert login_response.data["access"]
    assert login_response.data["refresh"]

    refresh_response = api_client.post(
        "/api/auth/token/refresh/",
        {"refresh": login_response.data["refresh"]},
        format="json",
    )

    assert refresh_response.status_code == 200
    assert refresh_response.data["access"]


def test_address_crud_is_scoped_to_authenticated_user(
    authenticated_client, user, other_user
):
    Address.objects.create(user=other_user, **address_payload(label="Other user"))

    create_response = authenticated_client.post(
        "/api/addresses/",
        address_payload(label="Home", line1="1 Main Street"),
        format="json",
    )

    assert create_response.status_code == 201
    address_id = create_response.data["id"]
    assert Address.objects.get(pk=address_id).user == user

    second_response = authenticated_client.post(
        "/api/addresses/",
        address_payload(label="Office", line1="200 Work Road", is_default=True),
        format="json",
    )

    assert second_response.status_code == 201
    assert Address.objects.get(pk=second_response.data["id"]).is_default is True
    assert Address.objects.get(pk=address_id).is_default is False

    list_response = authenticated_client.get("/api/addresses/")

    assert list_response.status_code == 200
    returned_ids = {item["id"] for item in paginated_items(list_response)}
    assert returned_ids == {address_id, second_response.data["id"]}

    update_response = authenticated_client.patch(
        f"/api/addresses/{address_id}/",
        {"city": "Brooklyn", "line2": ""},
        format="json",
    )

    assert update_response.status_code == 200
    assert update_response.data["city"] == "Brooklyn"
    assert Address.objects.get(pk=address_id).city == "Brooklyn"

    detail_response = authenticated_client.get(f"/api/addresses/{address_id}/")

    assert detail_response.status_code == 200
    assert detail_response.data["line1"] == "1 Main Street"

    delete_response = authenticated_client.delete(f"/api/addresses/{address_id}/")

    assert delete_response.status_code == 204
    assert not Address.objects.filter(pk=address_id).exists()


def test_catalog_filters_and_product_detail_return_active_merchandise(
    api_client, product_factory
):
    tees = Category.objects.create(name="T-Shirts")
    hoodies = Category.objects.create(name="Hoodies")
    naruto = AnimeFranchise.objects.create(name="Naruto")
    one_piece = AnimeFranchise.objects.create(name="One Piece")

    matching_product = product_factory(
        name="Naruto Black Tee",
        category=tees,
        franchise=naruto,
        base_price="29.90",
        is_featured=True,
        variants=[
            {
                "sku": "NARUTO-TEE-BLK-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 8,
            }
        ],
    )
    product_factory(
        name="One Piece Hoodie",
        category=hoodies,
        franchise=one_piece,
        base_price="59.90",
        variants=[
            {
                "sku": "ONEPIECE-HOODIE-RED-L",
                "size": ProductVariant.Size.L,
                "color": "Red",
                "stock_quantity": 4,
            }
        ],
    )
    product_factory(
        name="Archived Naruto Tee",
        category=tees,
        franchise=naruto,
        base_price="19.90",
        is_active=False,
        variants=[
            {
                "sku": "NARUTO-ARCHIVE-S",
                "size": ProductVariant.Size.S,
                "color": "Black",
                "stock_quantity": 10,
            }
        ],
    )

    list_response = api_client.get(
        "/api/products/",
        {
            "category": tees.slug,
            "franchise": naruto.slug,
            "min_price": "20",
            "max_price": "35",
            "size": ProductVariant.Size.M,
            "color": "black",
            "in_stock": "true",
        },
    )

    assert list_response.status_code == 200
    items = paginated_items(list_response)
    assert [item["slug"] for item in items] == [matching_product.slug]
    assert items[0]["category"]["slug"] == tees.slug
    assert items[0]["franchise"]["slug"] == naruto.slug
    assert items[0]["total_stock"] == 8

    detail_response = api_client.get(f"/api/products/{matching_product.slug}/")

    assert detail_response.status_code == 200
    assert detail_response.data["name"] == "Naruto Black Tee"
    assert detail_response.data["description"]
    assert detail_response.data["variants"][0]["sku"] == "NARUTO-TEE-BLK-M"

    inactive_response = api_client.get("/api/products/archived-naruto-tee/")

    assert inactive_response.status_code == 404


def test_cart_add_update_and_remove_item(authenticated_client, user, product_factory):
    product = product_factory(
        name="Gojo Oversized Tee",
        base_price="34.50",
        variants=[
            {
                "sku": "GOJO-TEE-WHT-M",
                "size": ProductVariant.Size.M,
                "color": "White",
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
    assert add_response.data["total_amount"] == "69.00"
    assert add_response.data["subtotal_amount"] == "69.00"
    assert add_response.data["items"][0]["quantity"] == 2
    assert add_response.data["items"][0]["unit_price"] == "34.50"
    assert add_response.data["items"][0]["line_total"] == "69.00"
    assert add_response.data["items"][0]["product"]["id"] == product.id
    assert add_response.data["items"][0]["product"]["slug"] == product.slug
    assert add_response.data["items"][0]["variant"]["sku"] == "GOJO-TEE-WHT-M"
    assert CartItem.objects.get(cart__user=user).quantity == 2

    item_id = cart_item_id(add_response, variant)
    update_response = authenticated_client.patch(
        f"/api/cart/items/{item_id}/",
        {"quantity": 4},
        format="json",
    )

    assert update_response.status_code == 200
    assert update_response.data["total_quantity"] == 4
    assert update_response.data["total_amount"] == "138.00"
    assert update_response.data["items"][0]["line_total"] == "138.00"
    assert CartItem.objects.get(pk=item_id).quantity == 4

    remove_response = authenticated_client.delete(f"/api/cart/items/{item_id}/")

    assert remove_response.status_code == 200
    assert remove_response.data["items"] == []
    assert remove_response.data["total_quantity"] == 0
    assert remove_response.data["total_amount"] == "0.00"
    assert remove_response.data["subtotal_amount"] == "0.00"
    assert not CartItem.objects.filter(pk=item_id).exists()


def test_checkout_creates_order_decrements_stock_and_clears_cart(
    authenticated_client, user, product_factory
):
    tee = product_factory(
        name="Spy Family Tee",
        base_price="25.00",
        variants=[
            {
                "sku": "SPY-TEE-GRN-M",
                "size": ProductVariant.Size.M,
                "color": "Green",
                "stock_quantity": 5,
            }
        ],
    )
    hoodie = product_factory(
        name="Chainsaw Hoodie",
        base_price="70.00",
        variants=[
            {
                "sku": "CHAINSAW-HOOD-BLK-L",
                "size": ProductVariant.Size.L,
                "color": "Black",
                "stock_quantity": 3,
                "price_delta": "5.00",
            }
        ],
    )
    tee_variant = tee.variants.get()
    hoodie_variant = hoodie.variants.get()

    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": tee_variant.id, "quantity": 2},
        format="json",
    )
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": hoodie_variant.id, "quantity": 1},
        format="json",
    )

    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 201
    assert checkout_response.data["status"] == "pending"
    assert checkout_response.data["total_amount"] == "125.00"
    assert len(checkout_response.data["items"]) == 2

    order = Order.objects.get(user=user)
    assert order.total_amount == Decimal("125.00")
    assert {item.sku for item in order.items.all()} == {
        "SPY-TEE-GRN-M",
        "CHAINSAW-HOOD-BLK-L",
    }

    detail_response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert detail_response.status_code == 200
    assert detail_response.data["total_amount"] == "125.00"
    assert detail_response.data["items_count"] == 3
    returned_items = {item["sku"]: item for item in detail_response.data["items"]}
    assert returned_items["SPY-TEE-GRN-M"]["product_name"] == "Spy Family Tee"
    assert returned_items["SPY-TEE-GRN-M"]["price_at_purchase"] == "25.00"
    assert returned_items["SPY-TEE-GRN-M"]["line_total"] == "50.00"
    assert returned_items["CHAINSAW-HOOD-BLK-L"]["line_total"] == "75.00"

    tee_variant.refresh_from_db()
    hoodie_variant.refresh_from_db()
    assert tee_variant.stock_quantity == 3
    assert hoodie_variant.stock_quantity == 2

    cart = Cart.objects.get(user=user)
    assert cart.items.count() == 0

    cart_response = authenticated_client.get("/api/cart/")
    assert cart_response.status_code == 200
    assert cart_response.data["total_quantity"] == 0
    assert cart_response.data["items"] == []


def test_checkout_rejects_empty_cart(authenticated_client, user):
    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 400
    assert checkout_response.data["cart"]["code"] == "cart_empty"
    assert checkout_response.data["cart"]["message"] == "Корзина пуста."
    assert not Order.objects.filter(user=user).exists()
    assert not CartItem.objects.filter(cart__user=user).exists()


def test_orders_list_and_detail_are_scoped_to_authenticated_user(
    authenticated_client, user, other_user, product_factory
):
    product = product_factory(
        name="Scoped Order Tee",
        base_price="21.00",
        variants=[
            {
                "sku": "SCOPED-TEE-BLK-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 3,
            }
        ],
    )
    variant = product.variants.get()
    own_order = Order.objects.create(
        user=user,
        total_amount=Decimal("42.00"),
        **shipping_payload(shipping_name="QA Shopper"),
    )
    OrderItem.objects.create(
        order=own_order,
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=2,
        price_at_purchase=Decimal("21.00"),
    )
    other_order = Order.objects.create(
        user=other_user,
        total_amount=Decimal("99.00"),
        **shipping_payload(shipping_name="Other Shopper"),
    )

    list_response = authenticated_client.get("/api/orders/")

    assert list_response.status_code == 200
    returned_ids = {item["id"] for item in paginated_items(list_response)}
    assert returned_ids == {own_order.id}
    assert other_order.id not in returned_ids

    own_detail_response = authenticated_client.get(f"/api/orders/{own_order.id}/")

    assert own_detail_response.status_code == 200
    assert own_detail_response.data["id"] == own_order.id
    assert own_detail_response.data["shipping_name"] == "QA Shopper"
    assert own_detail_response.data["items_count"] == 2
    assert own_detail_response.data["items"][0]["product_name"] == "Scoped Order Tee"
    assert own_detail_response.data["items"][0]["sku"] == "SCOPED-TEE-BLK-M"
    assert own_detail_response.data["items"][0]["line_total"] == "42.00"

    other_detail_response = authenticated_client.get(f"/api/orders/{other_order.id}/")

    assert other_detail_response.status_code == 404


def test_favorites_add_list_delete_and_idempotency(
    authenticated_client, user, other_user, product_factory
):
    product = product_factory(name="Favorite Eva Jacket", base_price="120.00")
    other_product = product_factory(name="Other Shopper Hoodie", base_price="88.00")
    inactive_product = product_factory(
        name="Archived Favorite Tee",
        base_price="24.00",
        is_active=False,
    )
    FavoriteProduct.objects.create(user=other_user, product=other_product)

    create_response = authenticated_client.post(
        "/api/favorites/",
        {"product_id": product.id},
        format="json",
    )

    assert create_response.status_code == 201
    assert create_response.data["created"] is True
    assert create_response.data["product_id"] == product.id
    assert create_response.data["product"]["slug"] == product.slug
    assert FavoriteProduct.objects.filter(user=user, product=product).count() == 1

    duplicate_response = authenticated_client.post(
        "/api/favorites/",
        {"product_id": product.id},
        format="json",
    )

    assert duplicate_response.status_code == 200
    assert duplicate_response.data["created"] is False
    assert duplicate_response.data["id"] == create_response.data["id"]
    assert FavoriteProduct.objects.filter(user=user, product=product).count() == 1

    inactive_response = authenticated_client.post(
        "/api/favorites/",
        {"product_id": inactive_product.id},
        format="json",
    )

    assert inactive_response.status_code == 404

    list_response = authenticated_client.get("/api/favorites/")

    assert list_response.status_code == 200
    returned_product_ids = {item["product_id"] for item in list_response.data}
    assert returned_product_ids == {product.id}
    assert other_product.id not in returned_product_ids

    delete_response = authenticated_client.delete(
        f"/api/favorites/products/{product.id}/"
    )

    assert delete_response.status_code == 200
    assert delete_response.data == {"product_id": product.id, "deleted": True}
    assert not FavoriteProduct.objects.filter(user=user, product=product).exists()
    assert FavoriteProduct.objects.filter(
        user=other_user, product=other_product
    ).exists()

    second_delete_response = authenticated_client.delete(
        f"/api/favorites/products/{product.id}/"
    )

    assert second_delete_response.status_code == 200
    assert second_delete_response.data == {"product_id": product.id, "deleted": False}


def test_checkout_rejects_overstock_without_creating_order_or_clearing_cart(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Low Stock Eva Tee",
        base_price="32.00",
        variants=[
            {
                "sku": "EVA-TEE-PUR-M",
                "size": ProductVariant.Size.M,
                "color": "Purple",
                "stock_quantity": 2,
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

    ProductVariant.objects.filter(pk=variant.pk).update(stock_quantity=1)

    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 400
    assert checkout_response.data["cart"]["code"] == "insufficient_stock"
    assert (
        checkout_response.data["cart"]["message"]
        == "Недостаточно товара на складе для артикула EVA-TEE-PUR-M."
    )
    assert not Order.objects.filter(user=user).exists()

    variant.refresh_from_db()
    assert variant.stock_quantity == 1

    cart = Cart.objects.get(user=user)
    assert cart.items.count() == 1
    assert cart.items.get().quantity == 2
