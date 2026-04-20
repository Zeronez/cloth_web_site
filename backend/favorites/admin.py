from django.contrib import admin

from favorites.models import FavoriteProduct


@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at", "product__category", "product__franchise")
    list_select_related = ("user", "product", "product__category", "product__franchise")
    search_fields = ("user__username", "user__email", "product__name")
