from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    def mark_email_verified(self):
        if self.email_verified_at is None:
            self.email_verified_at = timezone.now()
            self.save(update_fields=["email_verified_at"])


class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    label = models.CharField(max_length=64, default="Home")
    recipient_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32)
    country = models.CharField(max_length=80, default="US")
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=32)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(
                fields=["user", "is_default", "created_at"],
                name="users_addr_user_def_idx",
            ),
        ]

    def __str__(self):
        return f"{self.recipient_name}, {self.city}"
