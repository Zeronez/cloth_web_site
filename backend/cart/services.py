from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from catalog.models import ProductVariant


class CartValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CartLineInput:
    variant_id: int
    quantity: int


@dataclass(frozen=True)
class CartSnapshotItem:
    variant_id: int
    sku: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int


@dataclass(frozen=True)
class CartSnapshot:
    items: tuple[CartSnapshotItem, ...]
    total_quantity: int
    subtotal_cents: int


def _variant_unit_price_cents(variant):
    if hasattr(variant, "unit_price_cents"):
        return int(variant.unit_price_cents)
    price = getattr(variant, "price", Decimal("0.00"))
    return int(price * 100)


def build_cart_snapshot(lines, variant_lookup):
    merged = {}
    for line in lines:
        if line.quantity <= 0:
            raise CartValidationError("Quantity must be positive.")
        merged[line.variant_id] = merged.get(line.variant_id, 0) + line.quantity

    items = []
    subtotal_cents = 0
    total_quantity = 0
    for variant_id, quantity in merged.items():
        try:
            variant = variant_lookup(variant_id)
        except (KeyError, ProductVariant.DoesNotExist) as exc:
            raise CartValidationError(f"Unknown variant {variant_id}.") from exc
        if not getattr(variant, "is_active", True):
            raise CartValidationError(f"Variant {variant_id} is not active.")

        unit_price_cents = _variant_unit_price_cents(variant)
        line_total_cents = unit_price_cents * quantity
        items.append(
            CartSnapshotItem(
                variant_id=variant_id,
                sku=getattr(variant, "sku", ""),
                quantity=quantity,
                unit_price_cents=unit_price_cents,
                line_total_cents=line_total_cents,
            )
        )
        subtotal_cents += line_total_cents
        total_quantity += quantity

    return CartSnapshot(
        items=tuple(items),
        total_quantity=total_quantity,
        subtotal_cents=subtotal_cents,
    )


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


@transaction.atomic
def add_variant_to_cart(cart, variant_id, quantity):
    if quantity < 1:
        raise ValidationError({"quantity": "Quantity must be at least 1."})

    variant = (
        ProductVariant.objects.select_for_update()
        .select_related("product")
        .get(pk=variant_id)
    )
    if not variant.is_active or not variant.product.is_active:
        raise ValidationError({"variant": "This variant is not available."})

    item, _ = CartItem.objects.select_for_update().get_or_create(
        cart=cart,
        variant=variant,
        defaults={"quantity": 0},
    )
    requested_quantity = item.quantity + quantity
    if requested_quantity > variant.stock_quantity:
        raise ValidationError(
            {"quantity": "Requested quantity exceeds available stock."}
        )
    item.quantity = requested_quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item


@transaction.atomic
def set_cart_item_quantity(cart, item_id, quantity):
    item = (
        CartItem.objects.select_for_update()
        .select_related("variant")
        .get(pk=item_id, cart=cart)
    )
    if quantity < 1:
        item.delete()
        return None
    variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
    if quantity > variant.stock_quantity:
        raise ValidationError(
            {"quantity": "Requested quantity exceeds available stock."}
        )
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item
