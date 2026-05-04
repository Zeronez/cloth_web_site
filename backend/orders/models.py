from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

from catalog.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачен"
        PICKING = "picking", "На сборке"
        PACKED = "packed", "Упакован"
        SHIPPED = "shipped", "Передан в доставку"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"
        RETURNED = "returned", "Возвращён"

    TERMINAL_STATUSES = {
        Status.DELIVERED,
        Status.CANCELLED,
        Status.RETURNED,
    }
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.PAID, Status.CANCELLED},
        Status.PAID: {
            Status.PICKING,
            Status.PACKED,
            Status.SHIPPED,
            Status.CANCELLED,
            Status.RETURNED,
        },
        Status.PICKING: {
            Status.PACKED,
            Status.SHIPPED,
            Status.CANCELLED,
            Status.RETURNED,
        },
        Status.PACKED: {
            Status.SHIPPED,
            Status.CANCELLED,
            Status.RETURNED,
        },
        Status.SHIPPED: {
            Status.DELIVERED,
            Status.RETURNED,
        },
        Status.DELIVERED: {Status.RETURNED},
        Status.CANCELLED: set(),
        Status.RETURNED: set(),
    }

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
    idempotency_key = models.CharField(max_length=120, blank=True)
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
            models.Index(fields=["idempotency_key"], name="orders_idempo_key_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="unique_order_idempotency_per_user",
            )
        ]

    @property
    def is_terminal(self):
        return self.status in self.TERMINAL_STATUSES

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status, save=True):
        if new_status == self.status:
            return False
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Order cannot transition from {self.status} to {new_status}."
            )
        self.status = new_status
        if save:
            self.save(update_fields=["status", "updated_at"])
        return True

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
