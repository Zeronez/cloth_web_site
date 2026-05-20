from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Coupon(models.Model):
    class Kind(models.TextChoices):
        FIXED = "fixed", "Fixed discount"
        PERCENT = "percent", "Percent discount"
        FREE_SHIPPING = "free_shipping", "Free shipping"

    code = models.SlugField(max_length=48, unique=True)
    kind = models.CharField(max_length=24, choices=Kind.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percent = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="RUB")
    min_cart_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    max_redemptions = models.PositiveIntegerField(default=0)  # 0 = unlimited
    redeemed_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["is_active", "starts_at", "ends_at"],
                name="pricing_coupon_active_idx",
            ),
            models.Index(fields=["code"], name="pricing_coupon_code_idx"),
        ]

    def is_currently_active(self, *, now=None):
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now >= self.ends_at:
            return False
        if self.max_redemptions and self.redeemed_count >= self.max_redemptions:
            return False
        return True

    def __str__(self):
        return self.code


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(
        Coupon, related_name="redemptions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="coupon_redemptions",
        on_delete=models.CASCADE,
    )
    order = models.ForeignKey(
        "orders.Order",
        related_name="coupon_redemptions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["coupon", "user", "created_at"], name="pricing_coupon_user_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["coupon", "order"],
                condition=~Q(order=None),
                name="unique_coupon_redemption_per_order",
            )
        ]

    def __str__(self):
        return f"{self.coupon.code} -> {self.user_id}"


class GiftCard(models.Model):
    code = models.SlugField(max_length=48, unique=True)
    currency = models.CharField(max_length=3, default="RUB")
    initial_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["code"], name="pricing_gift_code_idx"),
            models.Index(fields=["expires_at"], name="pricing_gift_exp_idx"),
        ]

    def is_valid(self, *, now=None):
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.expires_at and now >= self.expires_at:
            return False
        return self.balance_amount > Decimal("0.00")

    def __str__(self):
        return self.code


class GiftCardRedemption(models.Model):
    gift_card = models.ForeignKey(
        GiftCard, related_name="redemptions", on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        "orders.Order", related_name="gift_card_redemptions", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.gift_card.code} {self.amount}"
