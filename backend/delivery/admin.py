from django.contrib import admin

from delivery.models import DeliveryMethod, OrderDeliverySnapshot


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "kind",
        "price_amount",
        "currency",
        "is_active",
        "sort_order",
    )
    list_filter = ("kind", "is_active", "currency")
    search_fields = ("code", "name")
    ordering = ("sort_order", "name")


@admin.register(OrderDeliverySnapshot)
class OrderDeliverySnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "method_code",
        "method_name",
        "price_amount",
        "currency",
        "created_at",
    )
    list_select_related = ("order", "delivery_method")
    search_fields = ("order__id", "method_code", "method_name", "recipient_phone")
    readonly_fields = (
        "order",
        "delivery_method",
        "method_code",
        "method_name",
        "method_kind",
        "price_amount",
        "currency",
        "estimated_days_min",
        "estimated_days_max",
        "recipient_name",
        "recipient_phone",
        "country",
        "city",
        "postal_code",
        "line1",
        "line2",
        "created_at",
    )
