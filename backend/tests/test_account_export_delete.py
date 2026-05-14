from decimal import Decimal

import pytest

from cart.models import CartItem
from favorites.models import FavoriteProduct
from notifications.models import NotificationLog
from orders.models import Order
from payments.models import Payment
from support.models import ContactRequest
from cart.models import Cart
from users.models import Address


pytestmark = pytest.mark.django_db


def shipping_payload(**overrides):
    payload = {
        "shipping_name": "QA Shopper",
        "shipping_phone": "+15551234567",
        "shipping_country": "RU",
        "shipping_city": "Москва",
        "shipping_postal_code": "101000",
        "shipping_line1": "Тестовая улица, 1",
        "shipping_line2": "",
    }
    payload.update(overrides)
    return payload


def test_account_export_returns_customer_data_bundle(
    authenticated_client, user, product_factory
):
    product = product_factory(name="Export Tee", base_price="44.00")
    variant = product.variants.get()
    Address.objects.create(
        user=user,
        label="Дом",
        recipient_name="QA Shopper",
        phone="+15551234567",
        country="RU",
        city="Москва",
        postal_code="101000",
        line1="Тестовая улица, 1",
        line2="",
        is_default=True,
    )
    favorite = FavoriteProduct.objects.create(user=user, product=product)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=2)
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("88.00"),
        status=Order.Status.DELIVERED,
        **shipping_payload(),
    )
    Payment.objects.create(
        order=order,
        user=user,
        method_code="local-card",
        provider_code="placeholder",
        amount=Decimal("88.00"),
        status=Payment.Status.SUCCEEDED,
    )
    ContactRequest.objects.create(
        user=user,
        name="QA Shopper",
        email=user.email,
        phone="+15551234567",
        topic=ContactRequest.Topic.ORDER,
        order_number=str(order.id),
        message="Хочу уточнить статус доставки по уже завершенному заказу.",
    )
    NotificationLog.objects.create(
        order=order,
        notification_type=NotificationLog.Type.ORDER_CREATED,
        channel=NotificationLog.Channel.EMAIL,
        status=NotificationLog.Status.DELIVERED,
        recipient=user.email,
        subject="Заказ создан",
        body="Ваш заказ принят в работу.",
    )

    response = authenticated_client.get("/api/v1/users/me/export/")

    assert response.status_code == 200
    assert response.data["profile"]["username"] == user.username
    assert response.data["addresses"][0]["label"] == "Дом"
    assert response.data["favorites"][0]["id"] == favorite.id
    assert response.data["cart"]["items"][0]["quantity"] == 2
    assert response.data["orders"][0]["id"] == order.id
    assert response.data["payments"][0]["status"] == Payment.Status.SUCCEEDED
    assert response.data["notifications"][0]["recipient"] == user.email
    assert response.data["contact_requests"][0]["email"] == user.email


def test_account_delete_requires_current_password(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/users/me/delete/",
        {"current_password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["details"]["current_password"][0]["code"] == "invalid"


def test_account_delete_rejects_active_orders(authenticated_client, user):
    Order.objects.create(
        user=user,
        total_amount=Decimal("50.00"),
        status=Order.Status.PENDING,
        **shipping_payload(),
    )

    response = authenticated_client.post(
        "/api/v1/users/me/delete/",
        {"current_password": "GhibliMerch!2026"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "open_orders_block_account_deletion"
    user.refresh_from_db()
    assert user.is_active is True


def test_account_delete_anonymizes_profile_and_preserves_commerce_history(
    authenticated_client, api_client, user, product_factory
):
    product = product_factory(name="Delete Me Tee", base_price="44.00")
    variant = product.variants.get()
    Address.objects.create(
        user=user,
        label="Дом",
        recipient_name="QA Shopper",
        phone="+15551234567",
        country="RU",
        city="Москва",
        postal_code="101000",
        line1="Тестовая улица, 1",
        line2="",
        is_default=True,
    )
    FavoriteProduct.objects.create(user=user, product=product)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("44.00"),
        status=Order.Status.DELIVERED,
        **shipping_payload(),
    )
    payment = Payment.objects.create(
        order=order,
        user=user,
        method_code="local-card",
        provider_code="placeholder",
        amount=Decimal("44.00"),
        status=Payment.Status.SUCCEEDED,
    )
    contact_request = ContactRequest.objects.create(
        user=user,
        name="QA Shopper",
        email=user.email,
        phone="+15551234567",
        topic=ContactRequest.Topic.ORDER,
        order_number=str(order.id),
        message="Хочу уточнить архив заказа перед удалением аккаунта.",
    )
    notification = NotificationLog.objects.create(
        order=order,
        notification_type=NotificationLog.Type.ORDER_CREATED,
        channel=NotificationLog.Channel.EMAIL,
        status=NotificationLog.Status.DELIVERED,
        recipient=user.email,
        subject="Заказ создан",
        body="Ваш заказ принят в работу.",
    )

    response = authenticated_client.post(
        "/api/v1/users/me/delete/",
        {"current_password": "GhibliMerch!2026"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    contact_request.refresh_from_db()
    notification.refresh_from_db()
    assert user.is_active is False
    assert user.is_account_deleted is True
    assert user.email == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.phone == ""
    assert user.username == f"deleted-user-{user.id}"
    assert user.has_usable_password() is False
    assert Address.objects.filter(user=user).count() == 0
    assert FavoriteProduct.objects.filter(user=user).count() == 0
    assert not hasattr(user, "cart")
    assert Order.objects.filter(user=user, id=order.id).exists()
    assert Payment.objects.filter(user=user, id=payment.id).exists()
    assert contact_request.user is None
    assert contact_request.email == f"deleted-user-{user.id}@example.invalid"
    assert contact_request.message == "Content removed after account deletion request."
    assert notification.recipient == f"deleted-user-{user.id}@example.invalid"
    assert notification.body == "Content removed after account deletion request."

    login_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": "shopper", "password": "GhibliMerch!2026"},
        format="json",
    )
    assert login_response.status_code == 401
