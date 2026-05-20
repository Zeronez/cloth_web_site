from django.db import models


class NotificationLog(models.Model):
    class Type(models.TextChoices):
        ORDER_CREATED = "order_created", "Заказ создан"
        ORDER_STATUS = "order_status", "Статус заказа"
        PAYMENT_STATUS = "payment_status", "Статус оплаты"
        SHIPPING_STATUS = "shipping_status", "Статус доставки"
        LOW_STOCK = "low_stock", "Низкий остаток"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает отправки"
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"
        DEAD_LETTERED = "dead_lettered", "Требует вмешательства"

    order = models.ForeignKey(
        "orders.Order",
        related_name="notification_logs",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    dedupe_key = models.CharField(max_length=160, blank=True)
    notification_type = models.CharField(max_length=32, choices=Type.choices)
    channel = models.CharField(
        max_length=16, choices=Channel.choices, default=Channel.EMAIL
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    error_message = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    dead_lettered_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order", "notification_type"],
                name="notifications_order_type_idx",
            ),
            models.Index(fields=["dedupe_key"], name="notifications_dedupe_key_idx"),
            models.Index(fields=["status"], name="notifications_status_idx"),
            models.Index(
                fields=["dead_lettered_at"],
                name="notif_log_dead_letter_idx",
            ),
            models.Index(
                fields=["processing_started_at"],
                name="notif_log_processing_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "notification_type", "channel"],
                condition=~models.Q(order=None),
                name="unique_notification_per_order_type_channel",
            ),
            models.UniqueConstraint(
                fields=["dedupe_key"],
                condition=~models.Q(dedupe_key=""),
                name="unique_notification_dedupe_key",
            ),
        ]

    def __str__(self):
        if self.order_id:
            return f"{self.notification_type} for order #{self.order_id}: {self.status}"
        return f"{self.notification_type} {self.dedupe_key}: {self.status}"


class NotificationAttempt(models.Model):
    class Status(models.TextChoices):
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"
        RETRY_SCHEDULED = "retry_scheduled", "Повтор запланирован"

    notification = models.ForeignKey(
        NotificationLog, related_name="attempts", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    provider_message_id = models.CharField(max_length=160, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["notification", "created_at"],
                name="notif_attempt_log_idx",
            ),
            models.Index(fields=["status"], name="notif_attempt_status_idx"),
        ]

    def __str__(self):
        return f"Attempt {self.status} for notification #{self.notification_id}"
