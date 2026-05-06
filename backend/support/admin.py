from django.contrib import admin

from support.models import ContactRequest
from users.staff_roles import (
    ROLE_ORDER_MANAGER,
    ROLE_OWNER,
    ROLE_SUPPORT_AGENT,
    user_has_staff_role,
)


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "status",
        "name",
        "email",
        "order_number",
        "created_at",
    )
    list_filter = ("status", "topic", "created_at")
    search_fields = ("name", "email", "phone", "order_number", "message")
    readonly_fields = (
        "user",
        "name",
        "email",
        "phone",
        "topic",
        "order_number",
        "message",
        "user_agent",
        "ip_address",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Обращение",
            {
                "fields": (
                    "status",
                    "topic",
                    "name",
                    "email",
                    "phone",
                    "order_number",
                    "message",
                )
            },
        ),
        ("Клиент", {"fields": ("user", "ip_address", "user_agent")}),
        ("Внутренняя работа", {"fields": ("admin_notes",)}),
        ("Служебное", {"fields": ("created_at", "updated_at")}),
    )

    def _can_access_support(self, user):
        return user_has_staff_role(
            user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
            ROLE_SUPPORT_AGENT,
        )

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return self._can_access_support(request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self._can_access_support(request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self._can_access_support(request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Register your models here.
