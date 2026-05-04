from django.contrib import admin

from delivery.models import DeliveryMethod, DeliveryTrackingEvent, OrderDeliverySnapshot


class DeliveryTrackingEventInline(admin.TabularInline):
    model = DeliveryTrackingEvent
    extra = 0
    can_delete = False
    readonly_fields = (
        "event_type",
        "previous_status",
        "new_status",
        "message",
        "location",
        "external_event_id",
        "happened_at",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "kind",
        "price_amount",
        "currency",
        "is_active",
        "sort_order",
    )
    list_filter = ("kind", "is_active", "currency")
    search_fields = ("code", "name")
    ordering = ("sort_order", "name")


@admin.register(OrderDeliverySnapshot)
class OrderDeliverySnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "method_code",
        "tracking_status",
        "provider_code",
        "external_shipment_id",
        "price_amount",
        "currency",
        "last_tracking_sync_at",
        "created_at",
    )
    list_filter = ("method_kind", "tracking_status", "provider_code", "created_at")
    list_select_related = ("order", "delivery_method")
    search_fields = (
        "order__id",
        "method_code",
        "method_name",
        "recipient_phone",
        "external_shipment_id",
    )
    readonly_fields = (
        "order",
        "delivery_method",
        "method_code",
        "method_name",
        "method_kind",
        "price_amount",
        "currency",
        "estimated_days_min",
        "estimated_days_max",
        "provider_code",
        "tracking_status",
        "external_shipment_id",
        "current_location",
        "last_tracking_sync_at",
        "recipient_name",
        "recipient_phone",
        "country",
        "city",
        "postal_code",
        "line1",
        "line2",
        "created_at",
    )
    inlines = [DeliveryTrackingEventInline]


@admin.register(DeliveryTrackingEvent)
class DeliveryTrackingEventAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot",
        "event_type",
        "new_status",
        "location",
        "external_event_id",
        "happened_at",
        "created_at",
    )
    list_filter = ("new_status", "event_type", "created_at")
    list_select_related = ("snapshot", "snapshot__order")
    search_fields = ("snapshot__order__id", "external_event_id", "location", "message")
    readonly_fields = (
        "snapshot",
        "event_type",
        "previous_status",
        "new_status",
        "message",
        "location",
        "payload",
        "external_event_id",
        "happened_at",
        "created_at",
    )
