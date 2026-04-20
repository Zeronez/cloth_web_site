from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.PROTECT
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.PENDING
    )
    track_number = models.CharField(max_length=120, blank=True)
    shipping_name = models.CharField(max_length=160)
    shipping_phone = models.CharField(max_length=32)
    shipping_country = models.CharField(max_length=80)
    shipping_city = models.CharField(max_length=120)
    shipping_postal_code = models.CharField(max_length=32)
    shipping_line1 = models.CharField(max_length=255)
    shipping_line2 = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="orders_orde_user_id_f64abd_idx",
            ),
            models.Index(fields=["created_at"], name="orders_orde_created_0fc1c0_idx"),
        ]

    def recalculate_total(self, save=True):
        total = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.total_amount = total
        if save:
            self.save(update_fields=["total_amount", "updated_at"])
        return total

    def __str__(self):
        return f"Order #{self.pk} {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, related_name="order_items", on_delete=models.PROTECT
    )
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=64)
    size = models.CharField(max_length=16)
    color = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [models.Index(fields=["sku"], name="orders_orde_sku_71777a_idx")]

    @property
    def line_total(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.sku} x {self.quantity}"
