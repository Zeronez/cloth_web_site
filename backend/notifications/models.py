from django.db import models


class NotificationLog(models.Model):
    class Type(models.TextChoices):
        ORDER_CREATED = "order_created", "Заказ создан"
        ORDER_STATUS = "order_status", "Статус заказа"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает отправки"
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"

    order = models.ForeignKey(
        "orders.Order", related_name="notification_logs", on_delete=models.CASCADE
    )
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order", "notification_type"],
                name="notifications_order_type_idx",
            ),
            models.Index(fields=["status"], name="notifications_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "notification_type", "channel"],
                name="unique_notification_per_order_type_channel",
            )
        ]

    def __str__(self):
        return f"{self.notification_type} for order #{self.order_id}: {self.status}"


class NotificationAttempt(models.Model):
    class Status(models.TextChoices):
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"

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
