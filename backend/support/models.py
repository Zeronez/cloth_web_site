from django.conf import settings
from django.db import models


class ContactRequest(models.Model):
    class Topic(models.TextChoices):
        ORDER = "order", "Вопрос по заказу"
        DELIVERY = "delivery", "Доставка"
        RETURN = "return", "Возврат или обмен"
        PRODUCT = "product", "Товар или размер"
        PARTNERSHIP = "partnership", "Партнерство"
        OTHER = "other", "Другое"

    class Status(models.TextChoices):
        NEW = "new", "Новое"
        IN_PROGRESS = "in_progress", "В работе"
        RESOLVED = "resolved", "Решено"
        SPAM = "spam", "Спам"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contact_requests",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    topic = models.CharField(max_length=32, choices=Topic.choices, default=Topic.OTHER)
    order_number = models.CharField(max_length=32, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW)
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="support_status_idx"),
            models.Index(fields=["email", "created_at"], name="support_email_idx"),
        ]

    def __str__(self):
        return f"{self.get_topic_display()} from {self.email}"


# Create your models here.
