from django.contrib import admin

from cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_key",
        "total_quantity",
        "total_amount",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "session_key")
    readonly_fields = ("total_quantity", "total_amount")
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity", "line_total")
    list_select_related = ("cart", "variant", "variant__product")
    search_fields = ("variant__sku", "variant__product__name")
