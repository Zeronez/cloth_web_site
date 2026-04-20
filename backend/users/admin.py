from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Address, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(User)
class AnimeAttireUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("AnimeAttire profile", {"fields": ("phone", "avatar")}),
    )
    list_display = ("username", "email", "phone", "is_staff", "is_active")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("recipient_name", "user", "city", "postal_code", "is_default")
    list_filter = ("country", "city", "is_default")
    search_fields = ("recipient_name", "phone", "city", "line1", "postal_code")
