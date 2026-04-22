from django.contrib import admin

from notifications.models import NotificationAttempt, NotificationLog


class NotificationAttemptInline(admin.TabularInline):
    model = NotificationAttempt
    extra = 0
    fields = ("status", "provider_message_id", "error_message", "created_at")
    readonly_fields = fields
    can_delete = False


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "notification_type",
        "channel",
        "status",
        "recipient",
        "delivered_at",
        "created_at",
    )
    list_filter = ("notification_type", "channel", "status", "created_at")
    search_fields = ("order__id", "recipient", "subject")
    readonly_fields = ("created_at", "updated_at", "delivered_at")
    inlines = [NotificationAttemptInline]


@admin.register(NotificationAttempt)
class NotificationAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification",
        "status",
        "provider_message_id",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("notification__order__id", "provider_message_id")
    readonly_fields = (
        "notification",
        "status",
        "provider_message_id",
        "error_message",
        "created_at",
    )
