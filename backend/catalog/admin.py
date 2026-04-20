from django.contrib import admin

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


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


@admin.register(AnimeFranchise)
class AnimeFranchiseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


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


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "size", "color", "stock_quantity", "is_active")
    list_filter = ("is_active", "size", "color", "product__category")
    list_select_related = ("product", "product__category")
    search_fields = ("sku", "product__name", "color")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("alt_text", "product", "is_main", "sort_order")
    list_filter = ("is_main",)
    list_select_related = ("product",)
    search_fields = ("alt_text", "product__name")
