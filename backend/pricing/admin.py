from django.contrib import admin

from pricing.models import Coupon, CouponRedemption, GiftCard, GiftCardRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "kind",
        "currency",
        "amount",
        "percent",
        "min_cart_amount",
        "per_user_limit",
        "max_redemptions",
        "redeemed_count",
        "is_active",
        "starts_at",
        "ends_at",
    )
    list_filter = ("kind", "currency", "is_active")
    search_fields = ("code",)


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "created_at")
    list_filter = ("coupon", "created_at")
    search_fields = ("coupon__code", "user__username", "user__email")


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("code", "currency", "initial_amount", "balance_amount", "is_active", "expires_at", "created_at")
    list_filter = ("currency", "is_active")
    search_fields = ("code",)


@admin.register(GiftCardRedemption)
class GiftCardRedemptionAdmin(admin.ModelAdmin):
    list_display = ("gift_card", "order", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("gift_card__code",)

