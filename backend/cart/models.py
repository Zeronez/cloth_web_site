from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="cart",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=80, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session_key"],
                condition=~models.Q(session_key=""),
                name="unique_guest_cart_session",
            )
        ]

    @property
    def total_amount(self):
        return sum(
            (item.line_total for item in self.items.select_related("variant__product")),
            Decimal("0.00"),
        )

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart #{self.pk}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, related_name="cart_items", on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"], name="unique_cart_variant"
            )
        ]

    @property
    def line_total(self):
        return self.variant.price * self.quantity

    def __str__(self):
        return f"{self.variant.sku} x {self.quantity}"
