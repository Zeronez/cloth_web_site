from django.contrib import admin, messages
from django.db.models import Q
from django.utils.html import format_html

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
    change_list_template = "admin/orders/order/change_list.html"
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
        "payment_status_badge",
        "delivery_status_badge",
        "fulfillment_next_step",
        "total_amount",
        "track_number",
        "created_at",
    )
    list_filter = (
        "status",
        "delivery_snapshot__method_code",
        "delivery_snapshot__provider_code",
        "delivery_snapshot__tracking_status",
        "created_at",
    )
    list_select_related = ("user", "delivery_snapshot")
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "delivery_snapshot").prefetch_related(
            "payments", "items"
        )

    def _get_delivery_snapshot(self, order):
        try:
            return order.delivery_snapshot
        except OrderDeliverySnapshot.DoesNotExist:
            return None

    def changelist_view(self, request, extra_context=None):
        queue_mode = request.GET.get("queue", "overview")
        mutable_get = request.GET.copy()
        mutable_get.pop("queue", None)
        request.GET = mutable_get
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, "context_data"):
            return response

        base_queryset = self.get_queryset(request)
        response.context_data["fulfillment_summary"] = self._build_fulfillment_summary(
            base_queryset
        )
        response.context_data["queue_mode"] = queue_mode
        response.context_data["queue_orders"] = self._build_queue_rows(
            base_queryset, queue_mode
        )
        response.context_data["queue_links"] = (
            ("overview", "Обзор"),
            ("picking", "На сборку"),
            ("packing", "На упаковку"),
            ("shipping", "К отгрузке"),
            ("issues", "Нужны действия"),
        )
        return response

    @admin.display(description="Оплата")
    def payment_status_badge(self, obj):
        payment = obj.payments.first()
        if payment is None:
            return format_html(
                '<span style="padding:2px 8px;border-radius:999px;'
                'background:#3f3f46;color:#fafafa;">{}</span>',
                "Без сессии",
            )
        palette = {
            "succeeded": ("#0f766e", "#ecfeff"),
            "authorized": ("#155e75", "#ecfeff"),
            "session_created": ("#92400e", "#fffbeb"),
            "pending": ("#92400e", "#fffbeb"),
            "failed": ("#991b1b", "#fef2f2"),
            "cancelled": ("#7f1d1d", "#fef2f2"),
            "refunded": ("#7f1d1d", "#fef2f2"),
            "expired": ("#7f1d1d", "#fef2f2"),
        }
        background, color = palette.get(payment.status, ("#312e81", "#eef2ff"))
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;'
            'background:{};color:{};">{}</span>',
            background,
            color,
            payment.get_status_display(),
        )

    @admin.display(description="Доставка")
    def delivery_status_badge(self, obj):
        snapshot = self._get_delivery_snapshot(obj)
        if snapshot is None:
            return format_html(
                '<span style="padding:2px 8px;border-radius:999px;'
                'background:#3f3f46;color:#fafafa;">{}</span>',
                "Нет snapshot",
            )
        palette = {
            "pending": ("#3f3f46", "#fafafa"),
            "created": ("#1d4ed8", "#eff6ff"),
            "handed_over": ("#155e75", "#ecfeff"),
            "in_transit": ("#7c3aed", "#f5f3ff"),
            "out_for_delivery": ("#b45309", "#fffbeb"),
            "delivered": ("#166534", "#f0fdf4"),
            "failed": ("#991b1b", "#fef2f2"),
            "returned": ("#7f1d1d", "#fef2f2"),
        }
        background, color = palette.get(
            snapshot.tracking_status, ("#312e81", "#eef2ff")
        )
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;'
            'background:{};color:{};">{}</span>',
            background,
            color,
            snapshot.get_tracking_status_display(),
        )

    @admin.display(description="Следующий шаг")
    def fulfillment_next_step(self, obj):
        snapshot = self._get_delivery_snapshot(obj)
        payment = obj.payments.first()
        if payment and payment.status in {"failed", "cancelled", "expired"}:
            return "Проверить оплату и связаться с клиентом"
        if obj.status == Order.Status.PAID:
            return "Передать на сборку"
        if obj.status == Order.Status.PICKING:
            return "Проверить SKU и упаковать"
        if obj.status == Order.Status.PACKED and (
            snapshot is None or not snapshot.external_shipment_id
        ):
            return "Создать отправку"
        if snapshot and snapshot.tracking_status == snapshot.TrackingStatus.CREATED:
            return "Передать перевозчику"
        if snapshot and snapshot.tracking_status == snapshot.TrackingStatus.FAILED:
            return "Разобрать проблему доставки"
        if obj.status == Order.Status.SHIPPED:
            return "Следить за трекингом"
        return "Контур в норме"

    def _build_fulfillment_summary(self, queryset):
        return {
            "paid_ready": queryset.filter(status=Order.Status.PAID).count(),
            "picking_queue": queryset.filter(
                status__in=[Order.Status.PAID, Order.Status.PICKING]
            ).count(),
            "packing_queue": queryset.filter(status=Order.Status.PACKED).count(),
            "awaiting_shipment": queryset.filter(
                status__in=[
                    Order.Status.PAID,
                    Order.Status.PICKING,
                    Order.Status.PACKED,
                ]
            )
            .filter(
                Q(delivery_snapshot__external_shipment_id="")
                | Q(delivery_snapshot__external_shipment_id__isnull=True)
            )
            .count(),
            "handoff_queue": queryset.filter(
                delivery_snapshot__tracking_status="created"
            ).count(),
            "delivery_issues": queryset.filter(
                delivery_snapshot__tracking_status="failed"
            ).count(),
        }

    def _build_queue_rows(self, queryset, queue_mode):
        if queue_mode == "picking":
            filtered = queryset.filter(
                status__in=[Order.Status.PAID, Order.Status.PICKING]
            )
        elif queue_mode == "packing":
            filtered = queryset.filter(status=Order.Status.PACKED)
        elif queue_mode == "shipping":
            filtered = queryset.filter(
                Q(delivery_snapshot__tracking_status="created")
                | Q(delivery_snapshot__tracking_status="handed_over")
            )
        elif queue_mode == "issues":
            filtered = queryset.filter(
                Q(delivery_snapshot__tracking_status="failed")
                | Q(payments__status__in=["failed", "cancelled", "expired"])
            ).distinct()
        else:
            filtered = queryset.filter(
                status__in=[
                    Order.Status.PAID,
                    Order.Status.PICKING,
                    Order.Status.PACKED,
                    Order.Status.SHIPPED,
                ]
            )

        return [
            {
                "order": order,
                "snapshot": self._get_delivery_snapshot(order),
                "next_step": self.fulfillment_next_step(order),
            }
            for order in filtered.order_by("-created_at")[:12]
        ]

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
