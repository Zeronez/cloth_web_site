from django.db.models.signals import pre_save
from django.dispatch import receiver

from catalog.models import Product, ProductPriceHistory


@receiver(pre_save, sender=Product)
def record_product_price_history(sender, instance: Product, **kwargs):
    if not instance.pk:
        return
    try:
        previous = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    tracked_fields = ("base_price", "sale_price")
    for field_name in tracked_fields:
        old_value = getattr(previous, field_name)
        new_value = getattr(instance, field_name)
        if old_value != new_value:
            ProductPriceHistory.objects.create(
                product=instance,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
            )

