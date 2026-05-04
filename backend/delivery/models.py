from django.db import models


class DeliveryMethod(models.Model):
    class Kind(models.TextChoices):
        COURIER = "courier", "Курьер"
        PICKUP = "pickup", "Самовывоз"
        POST = "post", "Почта"

    code = models.SlugField(max_length=48, unique=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.COURIER)
    description = models.TextField(blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    estimated_days_min = models.PositiveSmallIntegerField(null=True, blank=True)
    estimated_days_max = models.PositiveSmallIntegerField(null=True, blank=True)
    requires_address = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(
                fields=["is_active", "sort_order"],
                name="delivery_me_active_0e0e1c_idx",
            )
        ]

    def __str__(self):
        return self.name


class OrderDeliverySnapshot(models.Model):
    class TrackingStatus(models.TextChoices):
        PENDING = "pending", "Ожидает передачи"
        HANDED_OVER = "handed_over", "Передан в службу доставки"
        IN_TRANSIT = "in_transit", "В пути"
        OUT_FOR_DELIVERY = "out_for_delivery", "Курьер уже едет"
        DELIVERED = "delivered", "Доставлен"
        FAILED = "failed", "Проблема с доставкой"
        RETURNED = "returned", "Возвращается отправителю"

    order = models.OneToOneField(
        "orders.Order", related_name="delivery_snapshot", on_delete=models.CASCADE
    )
    delivery_method = models.ForeignKey(
        DeliveryMethod,
        related_name="order_snapshots",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    method_code = models.CharField(max_length=48)
    method_name = models.CharField(max_length=120)
    method_kind = models.CharField(max_length=24, choices=DeliveryMethod.Kind.choices)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    estimated_days_min = models.PositiveSmallIntegerField(null=True, blank=True)
    estimated_days_max = models.PositiveSmallIntegerField(null=True, blank=True)
    provider_code = models.SlugField(max_length=48, default="manual")
    tracking_status = models.CharField(
        max_length=24,
        choices=TrackingStatus.choices,
        default=TrackingStatus.PENDING,
    )
    external_shipment_id = models.CharField(max_length=120, blank=True)
    current_location = models.CharField(max_length=255, blank=True)
    last_tracking_sync_at = models.DateTimeField(null=True, blank=True)
    recipient_name = models.CharField(max_length=160)
    recipient_phone = models.CharField(max_length=32)
    country = models.CharField(max_length=80)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["method_code"], name="delivery_or_method_2bb933_idx"),
            models.Index(
                fields=["tracking_status"],
                name="delivery_or_tracki_2a5973_idx",
            ),
        ]

    def __str__(self):
        return f"{self.method_name} для заказа #{self.order_id}"


class DeliveryTrackingEvent(models.Model):
    snapshot = models.ForeignKey(
        OrderDeliverySnapshot,
        related_name="tracking_events",
        on_delete=models.CASCADE,
    )
    event_type = models.CharField(max_length=64)
    previous_status = models.CharField(
        max_length=24,
        choices=OrderDeliverySnapshot.TrackingStatus.choices,
        blank=True,
    )
    new_status = models.CharField(
        max_length=24,
        choices=OrderDeliverySnapshot.TrackingStatus.choices,
    )
    message = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    external_event_id = models.CharField(max_length=120, blank=True)
    happened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["snapshot", "created_at"],
                name="delivery_tr_snapsh_3ce87a_idx",
            ),
            models.Index(
                fields=["external_event_id"],
                name="delivery_tr_extern_1e9cb0_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "external_event_id"],
                condition=~models.Q(external_event_id=""),
                name="unique_delivery_tracking_external_id",
            )
        ]

    def __str__(self):
        return f"{self.event_type}: {self.previous_status}->{self.new_status}"
