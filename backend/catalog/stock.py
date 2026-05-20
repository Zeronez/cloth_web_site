from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from catalog.models import InventoryAdjustment, LowStockAlert, ProductVariant


LOW_STOCK_THRESHOLD = 3


class OptimisticLockError(ValueError):
    pass


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
    variant.stock_version += 1
    variant.save(update_fields=["stock_quantity", "stock_version", "updated_at"])
    adjustment = InventoryAdjustment.objects.create(
        variant=variant,
        performed_by=performed_by,
        reason=reason,
        delta=delta,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        note=note,
    )
    if getattr(settings, "LOW_STOCK_ALERTS_ENABLED", True) and is_low_stock(variant):
        alert = LowStockAlert.objects.create(
            variant=variant,
            threshold=LOW_STOCK_THRESHOLD,
            stock_quantity=variant.stock_quantity,
        )
        from notifications.tasks import send_low_stock_admin_email

        transaction.on_commit(lambda: send_low_stock_admin_email.delay(alert.id))
    return variant, adjustment


@transaction.atomic
def adjust_variant_stock_optimistic(
    *,
    variant_id,
    delta,
    expected_stock_version,
    reason,
    performed_by=None,
    note="",
):
    variant = ProductVariant.objects.get(pk=variant_id)
    previous_quantity = variant.stock_quantity
    if variant.stock_version != expected_stock_version:
        raise OptimisticLockError("Variant stock version is stale.")

    new_quantity = previous_quantity + delta
    if new_quantity < 0:
        raise ValidationError(
            {
                "stock_quantity": {
                    "code": "negative_inventory_forbidden",
                    "message": "РќРµР»СЊР·СЏ СѓРјРµРЅСЊС€РёС‚СЊ РѕСЃС‚Р°С‚РѕРє РЅРёР¶Рµ РЅСѓР»СЏ.",
                }
            }
        )

    updated = ProductVariant.objects.filter(
        pk=variant_id,
        stock_version=expected_stock_version,
    ).update(
        stock_quantity=new_quantity,
        stock_version=F("stock_version") + 1,
        updated_at=timezone.now(),
    )
    if updated != 1:
        raise OptimisticLockError("Variant stock version is stale.")

    variant.refresh_from_db()
    adjustment = InventoryAdjustment.objects.create(
        variant=variant,
        performed_by=performed_by,
        reason=reason,
        delta=delta,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        note=note,
    )
    if getattr(settings, "LOW_STOCK_ALERTS_ENABLED", True) and is_low_stock(variant):
        alert = LowStockAlert.objects.create(
            variant=variant,
            threshold=LOW_STOCK_THRESHOLD,
            stock_quantity=variant.stock_quantity,
        )
        from notifications.tasks import send_low_stock_admin_email

        transaction.on_commit(lambda: send_low_stock_admin_email.delay(alert.id))
    return variant, adjustment
from django.conf import settings
