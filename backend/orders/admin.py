from django.contrib import admin

from delivery.models import OrderDeliverySnapshot
from orders.models import Order, OrderItem
from payments.models import Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


class OrderDeliverySnapshotInline(admin.StackedInline):
    model = OrderDeliverySnapshot
    extra = 0
    can_delete = False
    readonly_fields = (
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

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    readonly_fields = (
        "method_code",
        "provider_code",
        "status",
        "amount",
        "currency",
        "external_payment_id",
        "session_expires_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total_amount",
        "track_number",
        "created_at",
    )
    list_filter = ("status", "created_at")
    list_select_related = ("user",)
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "track_number",
        "items__sku",
    )
    readonly_fields = ("total_amount",)
    inlines = [OrderDeliverySnapshotInline, PaymentInline, OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "sku",
        "product_name",
        "size",
        "color",
        "quantity",
        "price_at_purchase",
    )
    list_select_related = ("order", "variant")
    search_fields = ("sku", "product_name")
