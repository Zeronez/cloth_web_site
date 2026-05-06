from django.contrib import admin, messages

from catalog.models import (
    AnimeFranchise,
    Category,
    InventoryAdjustment,
    Product,
    ProductImage,
    ProductVariant,
)
from catalog.stock import LOW_STOCK_THRESHOLD, adjust_variant_stock, is_low_stock
from users.staff_roles import (
    ROLE_CATALOG_MANAGER,
    ROLE_INVENTORY_MANAGER,
    ROLE_OWNER,
    user_has_staff_role,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("sku", "size", "color", "stock_quantity", "price_delta", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_text", "is_main", "sort_order")


class LowStockListFilter(admin.SimpleListFilter):
    title = "низкий остаток"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Нужно пополнение"),
            ("no", "Остаток в норме"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD)
        if self.value() == "no":
            return queryset.filter(stock_quantity__gt=LOW_STOCK_THRESHOLD)
        return queryset


class InventoryAdjustmentInline(admin.TabularInline):
    model = InventoryAdjustment
    extra = 0
    can_delete = False
    fields = (
        "created_at",
        "performed_by",
        "reason",
        "delta",
        "previous_quantity",
        "new_quantity",
        "note",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AnimeFranchise)
class AnimeFranchiseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "franchise",
        "base_price",
        "is_active",
        "is_featured",
    )
    list_filter = ("is_active", "is_featured", "category", "franchise")
    list_select_related = ("category", "franchise")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "variants__sku")
    inlines = [ProductVariantInline, ProductImageInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "size",
        "color",
        "stock_badge",
        "is_active",
    )
    list_filter = (
        "is_active",
        "size",
        "color",
        "product__category",
        LowStockListFilter,
    )
    list_select_related = ("product", "product__category")
    search_fields = ("sku", "product__name", "color")
    inlines = [InventoryAdjustmentInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_CATALOG_MANAGER,
            ROLE_INVENTORY_MANAGER,
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or user_has_staff_role(
            request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER
        ):
            return ()
        return (
            "product",
            "sku",
            "size",
            "color",
            "stock_quantity",
            "price_delta",
            "is_active",
        )

    @admin.display(description="Остаток")
    def stock_badge(self, obj):
        if is_low_stock(obj):
            return f"{obj.stock_quantity} · low"
        return str(obj.stock_quantity)


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "reason",
        "delta",
        "previous_quantity",
        "new_quantity",
        "performed_by",
        "created_at",
    )
    list_filter = ("reason", "created_at")
    list_select_related = ("variant", "variant__product", "performed_by")
    search_fields = ("variant__sku", "variant__product__name", "note")
    fields = ("variant", "reason", "delta", "note")
    readonly_fields = (
        "performed_by",
        "previous_quantity",
        "new_quantity",
        "created_at",
        "updated_at",
    )

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_INVENTORY_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return
        variant, adjustment = adjust_variant_stock(
            variant_id=obj.variant_id,
            delta=obj.delta,
            reason=obj.reason,
            performed_by=request.user,
            note=obj.note,
        )
        obj.pk = adjustment.pk
        obj.variant = variant
        obj.performed_by = adjustment.performed_by
        obj.previous_quantity = adjustment.previous_quantity
        obj.new_quantity = adjustment.new_quantity
        obj.created_at = adjustment.created_at
        obj.updated_at = adjustment.updated_at
        self.message_user(
            request,
            f"Остаток {variant.sku} обновлён: {adjustment.previous_quantity} -> {adjustment.new_quantity}.",
            level=messages.SUCCESS,
        )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("alt_text", "product", "is_main", "sort_order")
    list_filter = ("is_main",)
    list_select_related = ("product",)
    search_fields = ("alt_text", "product__name")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
