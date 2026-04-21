from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from catalog.models import ProductVariant
from orders.models import Order, OrderItem


def _cart_error(code, message):
    return ValidationError({"cart": {"code": code, "message": message}})


@transaction.atomic
def checkout_cart(user, shipping_data):
    cart = (
        Cart.objects.select_for_update()
        .prefetch_related("items__variant__product")
        .get(user=user)
    )
    cart_items = list(cart.items.all())
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
    order = Order.objects.create(user=user, total_amount=0, **shipping_data)

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
    order.total_amount = total
    order.save(update_fields=["total_amount", "updated_at"])
    CartItem.objects.filter(cart=cart).delete()
    return order
