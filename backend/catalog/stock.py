from django.db import transaction
from rest_framework.exceptions import ValidationError

from catalog.models import InventoryAdjustment, ProductVariant


LOW_STOCK_THRESHOLD = 3


def is_low_stock(variant, threshold=LOW_STOCK_THRESHOLD):
    return variant.stock_quantity <= threshold


@transaction.atomic
def adjust_variant_stock(
    *,
    variant_id,
    delta,
    reason,
    performed_by=None,
    note="",
):
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    previous_quantity = variant.stock_quantity
    new_quantity = previous_quantity + delta
    if new_quantity < 0:
        raise ValidationError(
            {
                "stock_quantity": {
                    "code": "negative_inventory_forbidden",
                    "message": "Нельзя уменьшить остаток ниже нуля.",
                }
            }
        )

    variant.stock_quantity = new_quantity
    variant.save(update_fields=["stock_quantity", "updated_at"])
    adjustment = InventoryAdjustment.objects.create(
        variant=variant,
        performed_by=performed_by,
        reason=reason,
        delta=delta,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        note=note,
    )
    return variant, adjustment
