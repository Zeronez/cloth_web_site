from django.contrib import admin

from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "action",
        "app_label",
        "model",
        "object_id",
        "object_repr",
    )
    list_filter = ("action", "app_label", "model", "created_at")
    search_fields = ("actor__username", "actor__email", "object_id", "object_repr")
    date_hierarchy = "created_at"
    readonly_fields = (
        "actor",
        "action",
        "app_label",
        "model",
        "object_id",
        "object_repr",
        "changes",
        "snapshot",
        "metadata",
        "request_path",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
