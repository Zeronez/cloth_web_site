from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from cart.services import add_variant_to_cart
from catalog.models import ProductVariant
from orders.models import Order
from orders.services import checkout_cart


def shipping_payload(**overrides):
    payload = {
        "idempotency_key": "",
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


@pytest.mark.django_db(transaction=True)
def test_concurrent_checkout_allows_only_available_stock(
    user, other_user, product_factory
):
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent checkout locking contract is verified on PostgreSQL.")

    product = product_factory(
        name="Concurrent Checkout Tee",
        base_price="32.00",
        variants=[
            {
                "sku": "CONCURRENT-TEE-BLK-M",
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 3,
            }
        ],
    )
    variant = product.variants.get()

    for owner in (user, other_user):
        cart, _ = Cart.objects.get_or_create(user=owner)
        add_variant_to_cart(cart, variant.id, 2)

    start_barrier = Barrier(2)

    def run_checkout(user_id, key):
        close_old_connections()
        actor = get_user_model().objects.get(pk=user_id)
        start_barrier.wait(timeout=5)

        try:
            order, created = checkout_cart(
                actor, shipping_payload(idempotency_key=f"concurrent-{key}")
            )
            return {
                "status": "success",
                "user_id": actor.id,
                "order_id": order.id,
                "created": created,
            }
        except ValidationError as exc:
            return {
                "status": "error",
                "user_id": actor.id,
                "detail": exc.detail,
            }
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(run_checkout, user.id, "user-1")
        second_future = executor.submit(run_checkout, other_user.id, "user-2")
        results = [first_future.result(timeout=30), second_future.result(timeout=30)]

    successes = [result for result in results if result["status"] == "success"]
    failures = [result for result in results if result["status"] == "error"]

    assert len(successes) == 1
    assert len(failures) == 1

    failure = failures[0]
    assert failure["detail"]["cart"]["code"] == "insufficient_stock"
    assert "CONCURRENT-TEE-BLK-M" in failure["detail"]["cart"]["message"]

    winner_user_id = successes[0]["user_id"]
    loser_user_id = failures[0]["user_id"]

    variant.refresh_from_db()
    assert variant.stock_quantity == 1
    assert variant.stock_version == 1
    assert Order.objects.count() == 1
    assert Order.objects.get().user_id == winner_user_id

    assert CartItem.objects.filter(cart__user_id=winner_user_id).count() == 0
    loser_items = CartItem.objects.filter(cart__user_id=loser_user_id)
    assert loser_items.count() == 1
    assert loser_items.get().quantity == 2
