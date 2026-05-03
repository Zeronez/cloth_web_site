from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from catalog.models import ProductVariant
from delivery.services import (
    create_order_delivery_snapshot,
    delivery_price_for,
    resolve_delivery_method,
)
from orders.models import Order, OrderItem
from notifications.tasks import send_order_confirmation_email


def _cart_error(code, message):
    return ValidationError({"cart": {"code": code, "message": message}})


@transaction.atomic
def checkout_cart(user, shipping_data):
    shipping_data = dict(shipping_data)
    idempotency_key = shipping_data.pop("idempotency_key", "")
    if idempotency_key:
        existing_order = (
            Order.objects.select_for_update()
            .filter(user=user, idempotency_key=idempotency_key)
            .prefetch_related("items__variant")
            .first()
        )
        if existing_order:
            return existing_order, False

    delivery_method_code = shipping_data.pop("delivery_method_code", "")
    delivery_method = resolve_delivery_method(delivery_method_code)
    cart, _ = Cart.objects.select_for_update().get_or_create(user=user)
    if idempotency_key:
        existing_order = (
            Order.objects.select_for_update()
            .filter(user=user, idempotency_key=idempotency_key)
            .prefetch_related("items__variant")
            .first()
        )
        if existing_order:
            return existing_order, False

    cart_items = list(
        CartItem.objects.select_related("variant__product").filter(cart=cart)
    )
    if not cart_items:
        raise _cart_error("cart_empty", "Корзина пуста.")

    variant_ids = [item.variant_id for item in cart_items]
    locked_variants = {
        variant.id: variant
        for variant in ProductVariant.objects.select_for_update()
        .select_related("product")
        .filter(id__in=variant_ids)
    }

    total = Decimal("0.00")
    order = Order.objects.create(
        user=user,
        total_amount=0,
        idempotency_key=idempotency_key,
        **shipping_data,
    )

    order_items = []
    for item in cart_items:
        variant = locked_variants[item.variant_id]
        if not variant.is_active or not variant.product.is_active:
            raise _cart_error(
                "variant_unavailable",
                f"Товар с артикулом {variant.sku} больше недоступен.",
            )
        if item.quantity > variant.stock_quantity:
            raise _cart_error(
                "insufficient_stock",
                f"Недостаточно товара на складе для артикула {variant.sku}.",
            )

        price = variant.price
        total += price * item.quantity
        variant.stock_quantity -= item.quantity
        variant.save(update_fields=["stock_quantity", "updated_at"])

        order_items.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                quantity=item.quantity,
                price_at_purchase=price,
            )
        )

    OrderItem.objects.bulk_create(order_items)
    create_order_delivery_snapshot(order, delivery_method, shipping_data)
    order.total_amount = total + delivery_price_for(delivery_method)
    order.save(update_fields=["total_amount", "updated_at"])
    CartItem.objects.filter(cart=cart).delete()
    transaction.on_commit(lambda: send_order_confirmation_email.delay(order.id))
    return order, True
