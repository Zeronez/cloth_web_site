from django.contrib import admin

from delivery.models import DeliveryMethod, DeliveryTrackingEvent, OrderDeliverySnapshot
from users.staff_roles import (
    ROLE_ACCOUNTANT,
    ROLE_ORDER_MANAGER,
    ROLE_OWNER,
    ROLE_SUPPORT_AGENT,
    ROLE_WAREHOUSE_OPERATOR,
    user_has_staff_role,
)


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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_ORDER_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
            ROLE_WAREHOUSE_OPERATOR,
            ROLE_SUPPORT_AGENT,
            ROLE_ACCOUNTANT,
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or user_has_staff_role(
            request.user, ROLE_OWNER, ROLE_ORDER_MANAGER
        )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
            ROLE_WAREHOUSE_OPERATOR,
            ROLE_SUPPORT_AGENT,
            ROLE_ACCOUNTANT,
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
