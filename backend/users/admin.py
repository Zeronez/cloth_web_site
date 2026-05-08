from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from config.admin_exports import export_as_csv
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
    actions = ("export_customers_csv",)

    @admin.action(description="Экспортировать выбранных клиентов в CSV")
    def export_customers_csv(self, request, queryset):
        rows = []
        queryset = queryset.prefetch_related("orders")
        for user in queryset:
            rows.append(
                [
                    user.id,
                    user.username,
                    user.email,
                    user.phone,
                    user.first_name,
                    user.last_name,
                    user.is_active,
                    user.date_joined.isoformat(),
                    user.orders.count(),
                ]
            )
        return export_as_csv(
            filename="animeattire-customers.csv",
            headers=[
                "customer_id",
                "username",
                "email",
                "phone",
                "first_name",
                "last_name",
                "is_active",
                "date_joined",
                "orders_count",
            ],
            rows=rows,
        )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("recipient_name", "user", "city", "postal_code", "is_default")
    list_filter = ("country", "city", "is_default")
    search_fields = ("recipient_name", "phone", "city", "line1", "postal_code")
