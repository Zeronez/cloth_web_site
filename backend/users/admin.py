from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from audit.admin_mixins import AuditedModelAdminMixin
from audit.models import AuditLog
from audit.services import log_admin_event
from config.admin_exports import export_as_csv
from users.models import Address, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(User)
class AnimeAttireUserAdmin(AuditedModelAdminMixin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("AnimeAttire profile", {"fields": ("phone", "avatar")}),
    )
    list_display = ("username", "email", "phone", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("date_joined", "last_login")
    date_hierarchy = "date_joined"
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    inlines = [AddressInline]
    actions = ("export_customers_csv",)

    @admin.action(description="Экспортировать выбранных клиентов в CSV")
    def export_customers_csv(self, request, queryset):
        rows = []
        queryset = queryset.prefetch_related("orders")
        selected_count = queryset.count()
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
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=user,
                request=request,
                metadata={
                    "admin_action": "export_customers_csv",
                    "selected_count": selected_count,
                },
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
class AddressAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("recipient_name", "user", "city", "postal_code", "is_default")
    list_filter = ("country", "city", "is_default", "created_at", "updated_at")
    date_hierarchy = "created_at"
    search_fields = ("recipient_name", "phone", "city", "line1", "postal_code")
