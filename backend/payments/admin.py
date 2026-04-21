from django.contrib import admin

from payments.models import Payment, PaymentEvent, PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "provider_code",
        "session_mode",
        "currency",
        "is_active",
        "sort_order",
    )
    list_filter = ("session_mode", "provider_code", "is_active", "currency")
    search_fields = ("code", "name", "provider_code")
    ordering = ("sort_order", "name")


class PaymentEventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0
    can_delete = False
    readonly_fields = (
        "event_type",
        "previous_status",
        "new_status",
        "message",
        "payload",
        "external_event_id",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "user",
        "method_code",
        "provider_code",
        "status",
        "amount",
        "currency",
        "created_at",
    )
    list_filter = ("status", "provider_code", "currency", "created_at")
    list_select_related = ("order", "user", "method")
    search_fields = (
        "id",
        "order__id",
        "user__username",
        "user__email",
        "method_code",
        "external_payment_id",
        "idempotency_key",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = [PaymentEventInline]


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "event_type",
        "previous_status",
        "new_status",
        "created_at",
    )
    list_filter = ("event_type", "new_status", "created_at")
    list_select_related = ("payment",)
    search_fields = ("payment__id", "external_event_id", "message")
    readonly_fields = (
        "payment",
        "event_type",
        "previous_status",
        "new_status",
        "message",
        "payload",
        "external_event_id",
        "created_at",
    )
