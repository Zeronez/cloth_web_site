from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem
from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductRelation,
    ProductTag,
    ProductVariant,
)
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
        "privacy_policy_accepted": True,
        "offer_agreement_accepted": True,
    }

    register_response = api_client.post(
        "/api/auth/register/", registration, format="json"
    )

    assert register_response.status_code == 201
    assert register_response.data["username"] == "new-shopper"
    assert register_response.data["has_accepted_privacy_policy"] is True
    assert register_response.data["has_accepted_offer_agreement"] is True
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


def test_registration_rejects_duplicate_username_email_and_phone(api_client):
    user_model = get_user_model()
    user_model.objects.create_user(
        username="senko",
        email="senko@example.com",
        phone="+79824022646",
        password="StrongPass!2026",
    )

    response = api_client.post(
        "/api/auth/register/",
        {
            "username": "Senko",
            "email": "SENKO@example.com",
            "password": "StrongPass!2026",
            "first_name": "Senko",
            "last_name": "Fox",
            "phone": "8 (982) 402-26-46",
            "privacy_policy_accepted": True,
            "offer_agreement_accepted": True,
        },
        format="json",
    )

    assert response.status_code == 400
    error_details = response.data["error"]["details"]
    assert error_details["username"][0]["message"] == "Этот логин уже используется."
    assert error_details["email"][0]["message"] == "Этот email уже используется."
    assert error_details["phone"][0]["message"] == "Этот телефон уже используется."


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
    assert "tags" in items[0]

    detail_response = api_client.get(f"/api/products/{matching_product.slug}/")

    assert detail_response.status_code == 200
    assert detail_response.data["name"] == "Naruto Black Tee"
    assert detail_response.data["description"]
    assert detail_response.data["variants"][0]["sku"] == "NARUTO-TEE-BLK-M"
    assert "collections" not in detail_response.data
    assert "videos" not in detail_response.data
    assert "search_synonyms" not in detail_response.data
    assert "material" not in detail_response.data
    assert "fit" not in detail_response.data
    assert "care" not in detail_response.data
    assert "gender" not in detail_response.data
    assert "season" not in detail_response.data
    assert "weight_grams" not in detail_response.data
    assert "seo_title" not in detail_response.data
    assert "seo_description" not in detail_response.data

    inactive_response = api_client.get("/api/products/archived-naruto-tee/")

    assert inactive_response.status_code == 404


def test_catalog_search_matches_translated_tag_labels(api_client, product_factory):
    product = product_factory(name="Featured Search Tee")
    bestseller_tag = ProductTag.objects.create(name="Bestseller", slug="bestseller")
    product.tags.add(bestseller_tag)

    response = api_client.get("/api/products/", {"search": "Бестселлер"})

    assert response.status_code == 200
    items = paginated_items(response)
    assert [item["slug"] for item in items] == [product.slug]
    assert items[0]["tags"][0]["slug"] == "bestseller"
    assert items[0]["tags"][0]["label"] == "Бестселлер"


def test_user_can_manage_fit_profile(authenticated_client, user):
    update_response = authenticated_client.patch(
        "/api/v1/users/me/fit-profile/",
        {
            "height_cm": 182,
            "weight_kg": "78.5",
            "chest_cm": 101,
            "waist_cm": 84,
            "preferred_fit": "regular",
            "preferred_style": "streetwear",
            "preferred_season": "autumn",
            "tops_usual_size": "L",
            "budget_min_rub": 5000,
            "budget_max_rub": 20000,
        },
        format="json",
    )

    fetch_response = authenticated_client.get("/api/v1/users/me/fit-profile/")

    assert update_response.status_code == 200
    assert fetch_response.status_code == 200
    assert fetch_response.data["height_cm"] == 182
    assert fetch_response.data["preferred_style"] == "streetwear"
    assert fetch_response.data["budget_max_rub"] == 20000
    assert fetch_response.data["is_complete"] is True
    user.refresh_from_db()
    assert user.fit_profile["preferred_season"] == "autumn"


def test_product_detail_returns_richer_fit_recommendation_for_authenticated_user(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Recommendation Hoodie",
        description="Oversized hoodie for dark fantasy styling.",
        base_price="8900.00",
        variants=[
            {
                "sku": "RECO-HOODIE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 4,
            },
            {
                "sku": "RECO-HOODIE-L",
                "size": ProductVariant.Size.L,
                "color": "Black",
                "stock_quantity": 2,
            },
        ],
    )
    product.fit = "oversized"
    product.season = "winter"
    product.save(update_fields=["fit", "season", "updated_at"])
    product.tags.add(ProductTag.objects.create(name="Dark Fantasy", slug="dark-fantasy"))

    related_product = product_factory(
        name="Recommendation Tee",
        franchise=product.franchise,
        base_price="3200.00",
        description="Layer tee for dark fantasy looks.",
    )
    ProductRelation.objects.create(
        from_product=product,
        to_product=related_product,
        sort_order=1,
    )

    user.update_fit_profile(
        {
            "height_cm": 177,
            "weight_kg": "71.0",
            "chest_cm": 99,
            "waist_cm": 82,
            "preferred_fit": "regular",
            "preferred_style": "streetwear",
            "preferred_season": "winter",
            "tops_usual_size": "M",
            "budget_max_rub": 15000,
        }
    )

    response = authenticated_client.get(f"/api/v1/products/{product.slug}/")

    assert response.status_code == 200
    recommendation = response.data["fit_recommendation"]
    assert recommendation["recommended_size"] == "M"
    assert recommendation["profile_ready"] is True
    assert recommendation["summary"]
    assert recommendation["reasons"]
    assert recommendation["outfit"]["items"]


@pytest.mark.django_db
def test_product_list_returns_fit_recommendation_for_authenticated_user(
    authenticated_client,
    user,
    product_factory,
):
    user.update_fit_profile(
        {
            "height_cm": 178,
            "weight_kg": "74",
            "preferred_fit": "regular",
            "preferred_style": "streetwear",
            "tops_usual_size": "M",
        }
    )
    product = product_factory(
        name="Catalog Recommendation Hoodie",
        base_price="8900.00",
        description="Recommendation-ready hoodie.",
        variants=[
            {
                "sku": "CAT-REC-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
                "price_delta": "0.00",
                "is_active": True,
            }
        ],
    )
    product.slug = "catalog-recommendation-hoodie"
    product.fit = "regular"
    product.season = "autumn"
    product.status = Product.PublishingStatus.ACTIVE
    product.save(update_fields=["slug", "fit", "season", "status"])

    response = authenticated_client.get("/api/v1/products/")

    assert response.status_code == 200
    result = next(
        item
        for item in response.data["results"]
        if item["slug"] == "catalog-recommendation-hoodie"
    )
    assert result["fit_recommendation"]["recommended_size"] == "M"
    assert result["fit_recommendation"]["summary"]


def test_product_recommendation_endpoint_accepts_query_profile_override(
    api_client, product_factory
):
    product = product_factory(
        name="Query Recommendation Tee",
        description="Minimal tee for clean daily outfits.",
        variants=[
            {
                "sku": "QUERY-TEE-S",
                "size": ProductVariant.Size.S,
                "color": "White",
                "stock_quantity": 4,
            },
            {
                "sku": "QUERY-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "White",
                "stock_quantity": 4,
            },
        ],
    )

    response = api_client.get(
        f"/api/v1/products/{product.slug}/recommendation/",
        {
            "height_cm": 169,
            "weight_kg": "60.0",
            "chest_cm": 92,
            "preferred_fit": "regular",
            "preferred_style": "minimal",
        },
    )

    assert response.status_code == 200
    assert response.data["recommended_size"] in {"S", "M"}
    assert response.data["profile_ready"] is True
    assert response.data["missing_profile_fields"] == []


def test_archived_product_is_hidden_from_storefront_but_preserved_in_order_history(
    authenticated_client, api_client, user, product_factory
):
    product = product_factory(
        name="Archive Policy Hoodie",
        base_price="79.90",
        variants=[
            {
                "sku": "ARCHIVE-HOODIE-BLK-L",
                "size": ProductVariant.Size.L,
                "color": "Black",
                "stock_quantity": 4,
            }
        ],
    )
    variant = product.variants.get()
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("79.90"),
        **shipping_payload(),
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=1,
        price_at_purchase=Decimal("79.90"),
    )

    product.archive()
    product.refresh_from_db()
    variant.refresh_from_db()

    assert product.archived_at is not None
    assert product.is_active is False
    assert product.is_featured is False
    assert variant.is_active is False
    assert not Product.objects.filter(pk=product.pk, archived_at__isnull=True).exists()

    detail_response = api_client.get(f"/api/products/{product.slug}/")
    order_response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert detail_response.status_code == 404
    assert order_response.status_code == 200
    assert order_response.data["items"][0]["product_name"] == "Archive Policy Hoodie"
    assert order_response.data["items"][0]["sku"] == "ARCHIVE-HOODIE-BLK-L"


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
    assert "main_image" in add_response.data["items"][0]["product"]
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


def test_cart_rejects_quantity_update_for_archived_variant(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Archived Cart Tee",
        base_price="31.00",
        variants=[
            {
                "sku": "ARCHIVE-CART-BLK-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
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

    product.archive()
    item_id = cart_item_id(add_response, variant)

    update_response = authenticated_client.patch(
        f"/api/cart/items/{item_id}/",
        {"quantity": 2},
        format="json",
    )

    assert update_response.status_code == 400
    assert update_response.data["error"]["code"] == "validation_error"
    assert update_response.data["error"]["details"]["variant"] == [
        {"message": "This variant is not available.", "code": "invalid"}
    ]
    assert CartItem.objects.get(cart__user=user, variant=variant).quantity == 1


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
    assert returned_items["SPY-TEE-GRN-M"]["product"]["slug"] == tee.slug
    assert returned_items["SPY-TEE-GRN-M"]["price_at_purchase"] == "25.00"
    assert returned_items["SPY-TEE-GRN-M"]["line_total"] == "50.00"
    assert returned_items["CHAINSAW-HOOD-BLK-L"]["line_total"] == "75.00"

    tee_variant.refresh_from_db()
    hoodie_variant.refresh_from_db()
    assert tee_variant.stock_quantity == 3
    assert hoodie_variant.stock_quantity == 2
    assert tee_variant.stock_version == 1
    assert hoodie_variant.stock_version == 1

    cart = Cart.objects.get(user=user)
    assert cart.items.count() == 0

    cart_response = authenticated_client.get("/api/cart/")
    assert cart_response.status_code == 200
    assert cart_response.data["total_quantity"] == 0
    assert cart_response.data["items"] == []


def test_checkout_idempotency_key_returns_existing_order_without_second_stock_change(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Idempotent Checkout Tee",
        base_price="55.00",
        variants=[
            {
                "sku": "IDEMPOTENT-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
            }
        ],
    )
    variant = product.variants.get()
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 2},
        format="json",
    )
    payload = shipping_payload(idempotency_key="checkout-repeat-001")

    first_response = authenticated_client.post(
        "/api/orders/checkout/",
        payload,
        format="json",
    )
    second_response = authenticated_client.post(
        "/api/orders/checkout/",
        payload,
        format="json",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.data["id"] == first_response.data["id"]
    assert second_response.data["idempotency_key"] == "checkout-repeat-001"
    assert Order.objects.filter(user=user).count() == 1
    variant.refresh_from_db()
    assert variant.stock_quantity == 3
    assert variant.stock_version == 1
    assert Cart.objects.get(user=user).items.count() == 0


def test_checkout_rejects_empty_cart(authenticated_client, user):
    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 400
    assert checkout_response.data["error"]["code"] == "cart_empty"
    assert checkout_response.data["error"]["message"] == "Корзина пуста."
    assert checkout_response.data["error"]["details"]["cart"]["code"] == "cart_empty"
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
    assert own_detail_response.data["items"][0]["product"]["slug"] == product.slug
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


def test_archived_product_disappears_from_favorites_listing(
    authenticated_client, user, product_factory
):
    product = product_factory(name="Favorite Archive Tee", base_price="49.00")
    FavoriteProduct.objects.create(user=user, product=product)

    initial_response = authenticated_client.get("/api/favorites/")

    assert initial_response.status_code == 200
    assert [item["product"]["slug"] for item in initial_response.data] == [product.slug]

    product.archive()

    archived_response = authenticated_client.get("/api/favorites/")

    assert archived_response.status_code == 200
    assert archived_response.data == []


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
    assert checkout_response.data["error"]["code"] == "insufficient_stock"
    assert (
        checkout_response.data["error"]["message"]
        == "Недостаточно товара на складе для артикула EVA-TEE-PUR-M."
    )
    assert not Order.objects.filter(user=user).exists()

    variant.refresh_from_db()
    assert variant.stock_quantity == 1

    cart = Cart.objects.get(user=user)
    assert cart.items.count() == 1
    assert cart.items.get().quantity == 2


def test_checkout_rolls_back_order_and_stock_when_delivery_snapshot_creation_fails(
    authenticated_client, user, product_factory, monkeypatch
):
    product = product_factory(
        name="Rollback Snapshot Tee",
        base_price="32.00",
        variants=[
            {
                "sku": "ROLLBACK-TEE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 4,
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

    def fail_snapshot(*args, **kwargs):
        raise ValidationError(
            {
                "delivery": {
                    "code": "snapshot_failed",
                    "message": "Synthetic snapshot failure.",
                }
            }
        )

    monkeypatch.setattr("orders.services.create_order_delivery_snapshot", fail_snapshot)

    checkout_response = authenticated_client.post(
        "/api/orders/checkout/",
        shipping_payload(),
        format="json",
    )

    assert checkout_response.status_code == 400
    assert not Order.objects.filter(user=user).exists()
    variant.refresh_from_db()
    assert variant.stock_quantity == 4
    cart = Cart.objects.get(user=user)
    assert cart.items.count() == 1
    assert cart.items.get().quantity == 2
