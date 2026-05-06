from django.contrib import admin

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)
from users.staff_roles import ROLE_CATALOG_MANAGER, ROLE_OWNER, user_has_staff_role


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("sku", "size", "color", "stock_quantity", "price_delta", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_text", "is_main", "sort_order")


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
    list_display = ("sku", "product", "size", "color", "stock_quantity", "is_active")
    list_filter = ("is_active", "size", "color", "product__category")
    list_select_related = ("product", "product__category")
    search_fields = ("sku", "product__name", "color")

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
