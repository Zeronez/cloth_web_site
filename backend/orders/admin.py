from django.contrib import admin, messages

from delivery.services import (
    ensure_shipment_for_paid_order,
    refresh_order_tracking_from_provider,
)
from delivery.models import OrderDeliverySnapshot
from orders.models import Order, OrderItem
from payments.models import Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


class OrderDeliverySnapshotInline(admin.StackedInline):
    model = OrderDeliverySnapshot
    extra = 0
    can_delete = False
    readonly_fields = (
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

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    readonly_fields = (
        "method_code",
        "provider_code",
        "status",
        "amount",
        "currency",
        "external_payment_id",
        "session_expires_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    SHIPMENT_READY_STATUSES = {
        Order.Status.PAID,
        Order.Status.PICKING,
        Order.Status.PACKED,
        Order.Status.SHIPPED,
    }

    list_display = (
        "id",
        "user",
        "status",
        "total_amount",
        "track_number",
        "created_at",
    )
    list_filter = ("status", "created_at")
    list_select_related = ("user",)
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "track_number",
        "items__sku",
    )
    readonly_fields = ("total_amount",)
    inlines = [OrderDeliverySnapshotInline, PaymentInline, OrderItemInline]
    actions = (
        "create_shipment",
        "refresh_tracking",
        "mark_picking",
        "mark_packed",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
        "mark_returned",
    )

    @admin.action(description="Создать отправку")
    def create_shipment(self, request, queryset):
        created = 0
        skipped = 0
        failed = 0
        for order in queryset.select_related("user"):
            if order.status not in self.SHIPMENT_READY_STATUSES:
                skipped += 1
                continue
            try:
                _, was_created = ensure_shipment_for_paid_order(order=order)
            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"Заказ #{order.id}: не удалось создать отправку ({exc}).",
                    level=messages.ERROR,
                )
                continue
            if was_created:
                created += 1
            else:
                skipped += 1
        if created:
            self.message_user(
                request,
                f"Подготовлено отправок: {created}.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Пропущено заказов без новой отправки или в неподходящем статусе: {skipped}.",
                level=messages.WARNING,
            )
        if failed:
            self.message_user(
                request,
                f"Заказов с ошибкой создания отправки: {failed}.",
                level=messages.ERROR,
            )

    @admin.action(description="Обновить трекинг")
    def refresh_tracking(self, request, queryset):
        updated = 0
        skipped = 0
        failed = 0
        for order in queryset.select_related("user"):
            try:
                result = refresh_order_tracking_from_provider(order=order)
            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"Заказ #{order.id}: не удалось обновить трекинг ({exc}).",
                    level=messages.ERROR,
                )
                continue
            if result["updated"]:
                updated += 1
            else:
                skipped += 1
        if updated:
            self.message_user(
                request,
                f"Синхронизировано заказов: {updated}.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Без новых событий доставки: {skipped}.",
                level=messages.WARNING,
            )
        if failed:
            self.message_user(
                request,
                f"Заказов с ошибкой обновления трекинга: {failed}.",
                level=messages.ERROR,
            )

    @admin.action(description="Перевести в 'На сборке'")
    def mark_picking(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.PICKING)

    @admin.action(description="Перевести в 'Упакован'")
    def mark_packed(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.PACKED)

    @admin.action(description="Перевести в 'Передан в доставку'")
    def mark_shipped(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.SHIPPED)

    @admin.action(description="Перевести в 'Доставлен'")
    def mark_delivered(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.DELIVERED)

    @admin.action(description="Перевести в 'Отменён'")
    def mark_cancelled(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.CANCELLED)

    @admin.action(description="Перевести в 'Возвращён'")
    def mark_returned(self, request, queryset):
        self._transition_orders(request, queryset, Order.Status.RETURNED)

    def _transition_orders(self, request, queryset, new_status):
        updated = 0
        skipped = 0
        for order in queryset:
            try:
                changed = order.transition_to(new_status)
            except ValueError:
                skipped += 1
                continue
            if changed:
                updated += 1

        if updated:
            self.message_user(
                request,
                f"Обновлено заказов: {updated}. Новый статус: {dict(Order.Status.choices)[new_status]}.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Пропущено заказов из-за недопустимого перехода: {skipped}.",
                level=messages.WARNING,
            )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "sku",
        "product_name",
        "size",
        "color",
        "quantity",
        "price_at_purchase",
    )
    list_select_related = ("order", "variant")
    search_fields = ("sku", "product_name")
