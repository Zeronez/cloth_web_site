from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from cart.models import Cart, CartItem
from cart.tasks import cleanup_expired_guest_carts_task
from orders.models import Order
from payments.models import Payment, PaymentEvent, PaymentMethod
from payments.tasks import expire_stale_payment_sessions_task


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


def test_payment_timeout_task_expires_session_cancels_order_and_restores_stock(
    user, product_factory
):
    product = product_factory(
        name="Timeout Hoodie",
        base_price="80.00",
        variants=[{"sku": "TIMEOUT-HOODIE-BLK-L", "stock_quantity": 5}],
    )
    variant = product.variants.get()
    variant.stock_quantity = 2
    variant.stock_version = 4
    variant.save(update_fields=["stock_quantity", "stock_version", "updated_at"])
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Local card",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("160.00"),
        **shipping_payload(),
    )
    order.items.create(
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=2,
        price_at_purchase=Decimal("80.00"),
    )
    variant.stock_quantity = 0
    variant.stock_version = 5
    variant.save(update_fields=["stock_quantity", "stock_version", "updated_at"])
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency="RUB",
        status=Payment.Status.SESSION_CREATED,
        session_expires_at=timezone.now() - timedelta(minutes=5),
    )

    result = expire_stale_payment_sessions_task.run()

    payment.refresh_from_db()
    order.refresh_from_db()
    variant.refresh_from_db()

    assert result["expired_count"] == 1
    assert result["skipped_count"] == 0
    assert result["expired"][0]["payment_id"] == payment.id
    assert payment.status == Payment.Status.EXPIRED
    assert order.status == Order.Status.CANCELLED
    assert order.stock_restored_at is not None
    assert variant.stock_quantity == 2
    assert variant.stock_version == 6
    assert PaymentEvent.objects.filter(
        payment=payment,
        event_type="session_expired",
        new_status=Payment.Status.EXPIRED,
    ).exists()


def test_payment_timeout_task_is_idempotent_after_first_expiration(
    user, product_factory
):
    product = product_factory(
        name="Timeout Tee",
        base_price="40.00",
        variants=[{"sku": "TIMEOUT-TEE-BLK-M", "stock_quantity": 2}],
    )
    variant = product.variants.get()
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Local card",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("40.00"),
        **shipping_payload(),
    )
    order.items.create(
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=1,
        price_at_purchase=Decimal("40.00"),
    )
    variant.stock_quantity = 1
    variant.save(update_fields=["stock_quantity", "updated_at"])
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency="RUB",
        status=Payment.Status.SESSION_CREATED,
        session_expires_at=timezone.now() - timedelta(minutes=10),
    )

    first_result = expire_stale_payment_sessions_task.run()
    second_result = expire_stale_payment_sessions_task.run()

    payment.refresh_from_db()
    order.refresh_from_db()
    variant.refresh_from_db()

    assert first_result["expired_count"] == 1
    assert second_result["expired_count"] == 0
    assert payment.status == Payment.Status.EXPIRED
    assert order.status == Order.Status.CANCELLED
    assert variant.stock_quantity == 2
    assert (
        PaymentEvent.objects.filter(
            payment=payment, event_type="session_expired"
        ).count()
        == 1
    )


def test_payment_timeout_task_skips_non_pending_orders(user):
    method = PaymentMethod.objects.create(
        code="local-card",
        name="Local card",
        provider_code="placeholder",
        session_mode=PaymentMethod.SessionMode.PLACEHOLDER,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("125.00"),
        status=Order.Status.PAID,
        **shipping_payload(),
    )
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency="RUB",
        status=Payment.Status.SESSION_CREATED,
        session_expires_at=timezone.now() - timedelta(minutes=10),
    )

    result = expire_stale_payment_sessions_task.run()

    payment.refresh_from_db()
    order.refresh_from_db()

    assert result["expired_count"] == 0
    assert payment.status == Payment.Status.SESSION_CREATED
    assert order.status == Order.Status.PAID


def test_payment_timeout_task_uses_provider_status_before_local_expiry(
    settings, user, product_factory
):
    settings.PAYMENT_PROVIDER_STATUS_OVERRIDES = {
        "yookassa": {"provider-payment-1": "succeeded"}
    }
    product = product_factory(
        name="Provider Win Hoodie",
        base_price="90.00",
        variants=[{"sku": "PROVIDER-WIN-HOODIE", "stock_quantity": 4}],
    )
    variant = product.variants.get()
    method = PaymentMethod.objects.create(
        code="yookassa-card",
        name="YooKassa card",
        provider_code="yookassa",
        session_mode=PaymentMethod.SessionMode.REDIRECT,
    )
    order = Order.objects.create(
        user=user,
        total_amount=Decimal("90.00"),
        **shipping_payload(),
    )
    order.items.create(
        variant=variant,
        product_name=product.name,
        sku=variant.sku,
        size=variant.size,
        color=variant.color,
        quantity=1,
        price_at_purchase=Decimal("90.00"),
    )
    variant.stock_quantity = 3
    variant.save(update_fields=["stock_quantity", "updated_at"])
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        method_code=method.code,
        provider_code=method.provider_code,
        amount=order.total_amount,
        currency="RUB",
        external_payment_id="provider-payment-1",
        status=Payment.Status.SESSION_CREATED,
        session_expires_at=timezone.now() - timedelta(minutes=10),
    )

    result = expire_stale_payment_sessions_task.run()

    payment.refresh_from_db()
    order.refresh_from_db()
    variant.refresh_from_db()

    assert result["expired_count"] == 1
    assert result["expired"][0]["source"] == "provider_reconciliation"
    assert payment.status == Payment.Status.SUCCEEDED
    assert order.status == Order.Status.PAID
    assert order.stock_restored_at is None
    assert variant.stock_quantity == 3
    assert PaymentEvent.objects.filter(
        payment=payment,
        event_type="webhook_status_update",
        new_status=Payment.Status.SUCCEEDED,
    ).exists()


def test_cart_cleanup_task_deletes_only_expired_guest_carts(
    settings, user, product_factory
):
    settings.CART_GUEST_TTL_HOURS = 48
    now = timezone.now()
    product = product_factory(
        name="Cleanup Cap",
        base_price="25.00",
        variants=[{"sku": "CLEANUP-CAP-BLK", "stock_quantity": 10}],
    )
    variant = product.variants.get()
    expired_guest_cart = Cart.objects.create(session_key="expired-session")
    fresh_guest_cart = Cart.objects.create(session_key="fresh-session")
    user_cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=expired_guest_cart, variant=variant, quantity=2)
    CartItem.objects.create(cart=fresh_guest_cart, variant=variant, quantity=1)
    CartItem.objects.create(cart=user_cart, variant=variant, quantity=3)
    Cart.objects.filter(id=expired_guest_cart.id).update(
        updated_at=now - timedelta(hours=72)
    )
    Cart.objects.filter(id=fresh_guest_cart.id).update(
        updated_at=now - timedelta(hours=6)
    )
    Cart.objects.filter(id=user_cart.id).update(updated_at=now - timedelta(hours=96))

    result = cleanup_expired_guest_carts_task.run()

    assert result["deleted_carts"] == 1
    assert result["deleted_items"] == 1
    assert result["cart_ids"] == [expired_guest_cart.id]
    assert not Cart.objects.filter(id=expired_guest_cart.id).exists()
    assert Cart.objects.filter(id=fresh_guest_cart.id).exists()
    assert Cart.objects.filter(id=user_cart.id).exists()
    assert CartItem.objects.filter(cart=user_cart).count() == 1


def test_cart_cleanup_task_respects_batch_size(settings, product_factory):
    settings.CART_GUEST_TTL_HOURS = 1
    settings.CART_CLEANUP_BATCH_SIZE = 1
    now = timezone.now()
    product = product_factory(
        name="Cleanup Batch Tee",
        base_price="20.00",
        variants=[{"sku": "CLEANUP-BATCH-TEE", "stock_quantity": 10}],
    )
    variant = product.variants.get()
    older_cart = Cart.objects.create(session_key="older-session")
    newer_cart = Cart.objects.create(session_key="newer-session")
    CartItem.objects.create(cart=older_cart, variant=variant, quantity=1)
    CartItem.objects.create(cart=newer_cart, variant=variant, quantity=1)
    Cart.objects.filter(id=older_cart.id).update(updated_at=now - timedelta(hours=5))
    Cart.objects.filter(id=newer_cart.id).update(updated_at=now - timedelta(hours=4))

    first_result = cleanup_expired_guest_carts_task.run()

    assert first_result["deleted_carts"] == 1
    assert first_result["cart_ids"] == [older_cart.id]
    assert not Cart.objects.filter(id=older_cart.id).exists()
    assert Cart.objects.filter(id=newer_cart.id).exists()
