from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem
from favorites.models import FavoriteProduct
from orders.models import Order
from payments.models import Payment, PaymentMethod
from users.models import Address


pytestmark = pytest.mark.django_db


def address_payload(**overrides):
    payload = {
        "label": "Home",
        "recipient_name": "QA Shopper",
        "phone": "+79990001122",
        "country": "RU",
        "city": "Moscow",
        "postal_code": "101000",
        "line1": "Tverskaya 1",
        "line2": "",
        "is_default": False,
    }
    payload.update(overrides)
    return payload


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+79990001122",
        "shipping_country": "RU",
        "shipping_city": "Moscow",
        "shipping_postal_code": "101000",
        "shipping_line1": "Tverskaya 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


def create_payment_for_user(user, order=None):
    method, _ = PaymentMethod.objects.get_or_create(
        code="auth-card",
        defaults={
            "name": "Bank card",
            "provider_code": "placeholder",
            "session_mode": PaymentMethod.SessionMode.PLACEHOLDER,
        },
    )
    order = order or Order.objects.create(
        user=user,
        total_amount=Decimal("2500.00"),
        **shipping_payload(shipping_name=user.username),
    )
    return Payment.objects.create(
        user=user,
        order=order,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency=method.currency,
    )


def test_foreign_address_cannot_be_read_updated_or_deleted(
    authenticated_client, other_user
):
    address = Address.objects.create(user=other_user, **address_payload())

    detail_response = authenticated_client.get(f"/api/v1/addresses/{address.id}/")
    update_response = authenticated_client.patch(
        f"/api/v1/addresses/{address.id}/",
        {"city": "Kazan"},
        format="json",
    )
    delete_response = authenticated_client.delete(f"/api/v1/addresses/{address.id}/")

    assert detail_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    address.refresh_from_db()
    assert address.city == "Moscow"


def test_foreign_cart_item_cannot_be_updated_or_deleted(
    authenticated_client, user, other_user, product_factory
):
    variant = product_factory().variants.get()
    own_cart = Cart.objects.create(user=user)
    foreign_cart = Cart.objects.create(user=other_user)
    foreign_item = CartItem.objects.create(
        cart=foreign_cart,
        variant=variant,
        quantity=1,
    )

    update_response = authenticated_client.patch(
        f"/api/v1/cart/items/{foreign_item.id}/",
        {"quantity": 2},
        format="json",
    )
    delete_response = authenticated_client.delete(
        f"/api/v1/cart/items/{foreign_item.id}/"
    )

    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    foreign_item.refresh_from_db()
    assert foreign_item.quantity == 1
    assert Cart.objects.get(user=user).id == own_cart.id


def test_foreign_order_tracking_refresh_is_not_accessible(
    authenticated_client, other_user
):
    foreign_order = Order.objects.create(
        user=other_user,
        total_amount=Decimal("1200.00"),
        **shipping_payload(shipping_name="Other Shopper"),
    )

    response = authenticated_client.post(
        f"/api/v1/orders/{foreign_order.id}/tracking-refresh/"
    )

    assert response.status_code == 404


def test_favorite_product_delete_does_not_remove_another_users_favorite(
    authenticated_client, other_user, product_factory
):
    product = product_factory(name="Scoped Favorite Hoodie")
    favorite = FavoriteProduct.objects.create(user=other_user, product=product)

    response = authenticated_client.delete(f"/api/v1/favorites/products/{product.id}/")

    assert response.status_code == 200
    assert response.data == {"product_id": product.id, "deleted": False}
    assert FavoriteProduct.objects.filter(pk=favorite.pk).exists()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/orders/"),
        ("get", "/api/v1/orders/1/"),
        ("post", "/api/v1/orders/checkout/"),
        ("get", "/api/v1/addresses/"),
        ("post", "/api/v1/addresses/"),
        ("get", "/api/v1/payments/"),
        ("get", "/api/v1/payments/1/"),
        ("post", "/api/v1/payments/sessions/"),
        ("get", "/api/v1/payments/1/return-status/"),
        ("get", "/api/v1/favorites/"),
        ("post", "/api/v1/favorites/"),
    ],
)
def test_private_customer_endpoints_require_authentication(api_client, method, path):
    response = getattr(api_client, method)(path, {}, format="json")

    assert response.status_code == 401


def test_staff_api_user_does_not_inherit_customer_object_access(
    api_client, user, product_factory
):
    staff_user = get_user_model().objects.create_user(
        username="staff-api",
        email="staff-api@example.com",
        password="GhibliMerch!2026",
        is_staff=True,
    )
    product = product_factory(name="Customer Favorite Tee")
    Address.objects.create(user=user, **address_payload())
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("3300.00"),
        **shipping_payload(shipping_name="Customer"),
    )
    payment = create_payment_for_user(user, order=order)
    FavoriteProduct.objects.create(user=user, product=product)

    api_client.force_authenticate(user=staff_user)

    assert api_client.get("/api/v1/addresses/").data["results"] == []
    assert api_client.get("/api/v1/orders/").data["results"] == []
    assert api_client.get("/api/v1/payments/").data["results"] == []
    assert api_client.get("/api/v1/favorites/").data == []
    assert api_client.get(f"/api/v1/orders/{order.id}/").status_code == 404
    assert api_client.get(f"/api/v1/payments/{payment.id}/").status_code == 404


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/products/"),
        ("get", "/api/v1/categories/"),
        ("get", "/api/v1/franchises/"),
        ("get", "/api/v1/delivery-methods/"),
        ("get", "/api/v1/payment-methods/"),
        ("get", "/api/v1/cart/"),
        ("get", "/api/v1/health/live/"),
    ],
)
def test_public_endpoints_remain_public_after_default_permission_lockdown(
    api_client, method, path
):
    response = getattr(api_client, method)(path)

    assert response.status_code == 200
