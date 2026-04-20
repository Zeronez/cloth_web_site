from django.contrib import admin

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


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
    inlines = [OrderItemInline]


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
