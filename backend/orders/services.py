from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from catalog.models import InventoryAdjustment
from catalog.stock import adjust_variant_stock
from cart.models import Cart, CartItem
from catalog.models import ProductVariant
from delivery.services import (
    create_order_delivery_snapshot,
    delivery_price_for,
    resolve_delivery_method,
)
from orders.models import Order, OrderItem
from notifications.tasks import send_order_confirmation_email
from pricing.models import Coupon, GiftCard
from pricing.services import compute_totals, redeem_coupon


def _cart_error(code, message):
    return ValidationError({"cart": {"code": code, "message": message}})


def _consent_error(code, message):
    return ValidationError({"consent": {"code": code, "message": message}})


@transaction.atomic
def restore_order_stock(
    *, order, reason=InventoryAdjustment.Reason.RETURN, note="", performed_by=None
):
    locked_order = (
        Order.objects.select_for_update()
        .prefetch_related("items__variant")
        .get(pk=order.pk)
    )
    if locked_order.stock_restored_at is not None:
        return False

    for item in locked_order.items.all():
        adjust_variant_stock(
            variant_id=item.variant_id,
            delta=item.quantity,
            reason=reason,
            performed_by=performed_by,
            note=note
            or f"Возврат остатка по заказу #{locked_order.id} для SKU {item.sku}.",
        )

    locked_order.stock_restored_at = timezone.now()
    locked_order.save(update_fields=["stock_restored_at", "updated_at"])
    return True


@transaction.atomic
def transition_order_status(
    *,
    order,
    new_status,
    performed_by=None,
    restock_on_cancel=False,
    restock_note="",
):
    locked_order = (
        Order.objects.select_for_update()
        .prefetch_related("items__variant")
        .get(pk=order.pk)
    )
    old_status = locked_order.status
    changed = locked_order.transition_to(new_status)
    was_restocked = False
    if changed and new_status == Order.Status.CANCELLED and restock_on_cancel:
        was_restocked = restore_order_stock(
            order=locked_order,
            reason=InventoryAdjustment.Reason.RETURN,
            note=restock_note,
            performed_by=performed_by,
        )
    return locked_order, changed, old_status, was_restocked


@transaction.atomic
def confirm_order_return_received(*, order, performed_by=None, note=""):
    locked_order = Order.objects.select_for_update().get(pk=order.pk)
    if locked_order.status != Order.Status.RETURNED:
        raise ValidationError(
            {
                "order": {
                    "code": "return_confirmation_invalid_status",
                    "message": "Подтвердить приемку возврата можно только для заказа в статусе 'Возвращён'.",
                }
            }
        )

    return restore_order_stock(
        order=locked_order,
        reason=InventoryAdjustment.Reason.RETURN,
        note=note
        or f"Подтверждена приемка возврата заказа #{locked_order.id} на склад.",
        performed_by=performed_by,
    )


@transaction.atomic
def checkout_cart(user, shipping_data):
    if not user.has_accepted_privacy_policy or (
        user.privacy_policy_version != settings.PRIVACY_POLICY_VERSION
    ):
        raise _consent_error(
            "privacy_policy_reaccept_required",
            "Перед оформлением заказа нужно принять актуальную политику конфиденциальности.",
        )
    if not user.has_accepted_offer_agreement or (
        user.offer_agreement_version != settings.OFFER_AGREEMENT_VERSION
    ):
        raise _consent_error(
            "offer_agreement_reaccept_required",
            "Перед оформлением заказа нужно принять актуальную оферту.",
        )

    shipping_data = dict(shipping_data)
    idempotency_key = shipping_data.pop("idempotency_key", "")
    coupon_code = (shipping_data.pop("coupon_code", "") or "").strip()
    gift_card_code = (shipping_data.pop("gift_card_code", "") or "").strip()
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
    delivery_method = resolve_delivery_method(
        delivery_method_code,
        country=shipping_data.get("shipping_country", ""),
        city=shipping_data.get("shipping_city", ""),
        postal_code=shipping_data.get("shipping_postal_code", ""),
    )
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
    items_subtotal = Decimal("0.00")
    currency = delivery_method.currency if delivery_method is not None else "RUB"
    order = Order.objects.create(
        user=user,
        currency=currency,
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
        line_total = price * item.quantity
        items_subtotal += line_total
        total += line_total
        variant.stock_quantity -= item.quantity
        variant.stock_version += 1
        variant.save(update_fields=["stock_quantity", "stock_version", "updated_at"])

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
    delivery_amount = (
        delivery_price_for(
            delivery_method,
            country=shipping_data.get("shipping_country", ""),
            city=shipping_data.get("shipping_city", ""),
            postal_code=shipping_data.get("shipping_postal_code", ""),
        )
        if delivery_method is not None
        else Decimal("0.00")
    )

    coupon = None
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon is None:
            raise ValidationError(
                {"coupon": {"code": "coupon_not_found", "message": "Купон не найден."}}
            )

    totals = compute_totals(
        currency=currency,
        items_subtotal=items_subtotal,
        delivery=delivery_amount,
        coupon=coupon,
        user=user,
    )
    order.items_subtotal_amount = totals.items_subtotal
    order.discount_amount = totals.discount
    order.delivery_amount = totals.delivery
    order.tax_amount = totals.tax
    order.fiscal_fee_amount = Decimal("0.00")
    order.total_amount = totals.total
    if coupon is not None:
        order.coupon = coupon
    order.save(
        update_fields=[
            "currency",
            "items_subtotal_amount",
            "discount_amount",
            "delivery_amount",
            "tax_amount",
            "fiscal_fee_amount",
            "coupon",
            "total_amount",
            "updated_at",
        ]
    )
    if coupon is not None:
        redeem_coupon(coupon=coupon, user=user, order=order)

    if gift_card_code:
        gift_card = GiftCard.objects.filter(code__iexact=gift_card_code).first()
        if gift_card is None or not gift_card.is_valid():
            raise ValidationError(
                {
                    "gift_card": {
                        "code": "gift_card_invalid",
                        "message": "Подарочная карта недоступна.",
                    }
                }
            )
        if gift_card.currency != order.currency:
            raise ValidationError(
                {
                    "gift_card": {
                        "code": "currency_mismatch",
                        "message": "Подарочная карта в другой валюте.",
                    }
                }
            )
        apply_amount = min(gift_card.balance_amount, order.total_amount)
        gift_card.balance_amount -= apply_amount
        gift_card.save(update_fields=["balance_amount", "updated_at"])
        from pricing.models import GiftCardRedemption

        GiftCardRedemption.objects.create(
            gift_card=gift_card,
            order=order,
            amount=apply_amount,
        )
        order.discount_amount = (order.discount_amount or Decimal("0.00")) + apply_amount
        order.total_amount = max(Decimal("0.00"), order.total_amount - apply_amount)
        order.save(update_fields=["discount_amount", "total_amount", "updated_at"])

    CartItem.objects.filter(cart=cart).delete()
    transaction.on_commit(lambda: send_order_confirmation_email.delay(order.id))
    return order, True
