import pytest

from catalog.models import ProductVariant


pytestmark = pytest.mark.django_db


def test_v1_catalog_matches_legacy_catalog(api_client, product_factory):
    product = product_factory(name="Versioned Eva Tee")

    legacy_response = api_client.get("/api/products/")
    v1_response = api_client.get("/api/v1/products/")

    assert legacy_response.status_code == 200
    assert v1_response.status_code == 200
    assert legacy_response.data["count"] == v1_response.data["count"] == 1
    assert v1_response.data["results"][0]["slug"] == product.slug


def test_v1_product_detail_keeps_zero_stock_active_sizes_visible(
    api_client, product_factory
):
    product = product_factory(
        name="Versioned Stock Matrix Hoodie",
        variants=[
            {
                "sku": "MATRIX-HOODIE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 3,
                "is_active": True,
            },
            {
                "sku": "MATRIX-HOODIE-L",
                "size": ProductVariant.Size.L,
                "color": "Black",
                "stock_quantity": 0,
                "is_active": True,
            },
            {
                "sku": "MATRIX-HOODIE-XL",
                "size": ProductVariant.Size.XL,
                "color": "Black",
                "stock_quantity": 5,
                "is_active": False,
            },
        ],
    )

    response = api_client.get(f"/api/v1/products/{product.slug}/")

    assert response.status_code == 200
    variant_skus = [variant["sku"] for variant in response.data["variants"]]
    assert "MATRIX-HOODIE-M" in variant_skus
    assert "MATRIX-HOODIE-L" in variant_skus
    assert "MATRIX-HOODIE-XL" not in variant_skus


def test_v1_auth_and_user_profile_flow(api_client):
    register_response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "versioned-shopper",
            "email": "versioned@example.com",
            "password": "GhibliMerch!2026",
            "first_name": "Versioned",
            "last_name": "Shopper",
            "phone": "+79991234567",
        },
        format="json",
    )
    token_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": "versioned-shopper", "password": "GhibliMerch!2026"},
        format="json",
    )

    assert register_response.status_code == 201
    assert token_response.status_code == 200

    profile_response = api_client.get(
        "/api/v1/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}",
    )

    assert profile_response.status_code == 200
    assert profile_response.data["username"] == "versioned-shopper"


def test_v1_cart_checkout_path_uses_same_stock_transaction_contract(
    authenticated_client, user, product_factory
):
    product = product_factory(
        name="Versioned Checkout Hoodie",
        base_price="50.00",
        variants=[
            {
                "sku": "VERSIONED-HOODIE-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 2,
            }
        ],
    )
    variant = product.variants.get()

    add_response = authenticated_client.post(
        "/api/v1/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    checkout_response = authenticated_client.post(
        "/api/v1/orders/checkout/",
        {
            "shipping_name": "QA Shopper",
            "shipping_phone": "+79991234567",
            "shipping_country": "RU",
            "shipping_city": "Москва",
            "shipping_postal_code": "101000",
            "shipping_line1": "Тестовая улица, 1",
            "shipping_line2": "",
        },
        format="json",
    )

    assert add_response.status_code == 201
    assert checkout_response.status_code == 201
    assert checkout_response.data["items"][0]["sku"] == "VERSIONED-HOODIE-M"
    variant.refresh_from_db()
    assert variant.stock_quantity == 1


def test_v1_error_contract_matches_standard_envelope(api_client):
    response = api_client.get("/api/v1/users/me/")

    assert response.status_code == 401
    assert response.data["error"]["code"] == "not_authenticated"
    assert response.data["error"]["status"] == 401
    assert response.data["error"]["request_id"]


def test_v1_schema_and_docs_are_available(client):
    schema_response = client.get("/api/v1/schema/", HTTP_ACCEPT="application/json")
    docs_response = client.get("/api/v1/docs/")
    redoc_response = client.get("/api/v1/redoc/")

    assert schema_response.status_code == 200
    assert "/api/v1/products/" in schema_response.json()["paths"]
    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200
