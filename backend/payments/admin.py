from django.contrib import admin

from audit.admin_mixins import AuditedModelAdminMixin
from audit.models import AuditLog
from audit.services import log_admin_event
from config.admin_exports import export_as_csv
from payments.models import Payment, PaymentEvent, PaymentMethod, PaymentRefund
from users.staff_roles import (
    ROLE_ACCOUNTANT,
    ROLE_ORDER_MANAGER,
    ROLE_OWNER,
    ROLE_SUPPORT_AGENT,
    user_has_staff_role,
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "provider_code",
        "session_mode",
        "currency",
        "is_active",
        "sort_order",
    )
    list_filter = (
        "session_mode",
        "provider_code",
        "is_active",
        "currency",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    search_fields = ("code", "name", "provider_code")
    ordering = ("sort_order", "name")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
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


class PaymentRefundInline(admin.TabularInline):
    model = PaymentRefund
    extra = 0
    fields = (
        "amount",
        "currency",
        "status",
        "external_refund_id",
        "message",
        "created_at",
    )
    readonly_fields = fields
    can_delete = False


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
        "refunded_amount",
        "currency",
        "created_at",
    )
    list_filter = (
        "status",
        "method_code",
        "provider_code",
        "currency",
        "order__status",
        "session_expires_at",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
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
    readonly_fields = (
        "order",
        "user",
        "method",
        "method_code",
        "provider_code",
        "status",
        "amount",
        "refunded_amount",
        "currency",
        "external_payment_id",
        "idempotency_key",
        "session_expires_at",
        "created_at",
        "updated_at",
    )
    inlines = [PaymentRefundInline, PaymentEventInline]
    actions = ("export_payments_csv",)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
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

    @admin.action(description="Экспортировать выбранные платежи в CSV")
    def export_payments_csv(self, request, queryset):
        rows = []
        queryset = queryset.select_related("order", "user")
        selected_count = queryset.count()
        for payment in queryset:
            rows.append(
                [
                    payment.id,
                    payment.order_id,
                    payment.user.email,
                    payment.method_code,
                    payment.provider_code,
                    payment.status,
                    payment.amount,
                    payment.currency,
                    payment.external_payment_id,
                    payment.created_at.isoformat(),
                ]
            )
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=payment,
                request=request,
                metadata={
                    "admin_action": "export_payments_csv",
                    "selected_count": selected_count,
                },
            )
        return export_as_csv(
            filename="animeattire-payments.csv",
            headers=[
                "payment_id",
                "order_id",
                "customer_email",
                "method_code",
                "provider_code",
                "status",
                "amount",
                "currency",
                "external_payment_id",
                "created_at",
            ],
            rows=rows,
        )


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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
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
