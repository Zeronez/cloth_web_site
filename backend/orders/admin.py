from django.contrib import admin, messages
from django.db.models import Q
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from delivery.services import (
    ensure_shipment_for_paid_order,
    refresh_order_tracking_from_provider,
)
from delivery.models import OrderDeliverySnapshot
from orders.models import Order, OrderItem
from payments.models import Payment
from users.staff_roles import (
    ROLE_ORDER_MANAGER,
    ROLE_OWNER,
    ROLE_SUPPORT_AGENT,
    ROLE_WAREHOUSE_OPERATOR,
    user_has_staff_role,
)


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
    SUPPORT_EDITABLE_FIELDS = {"internal_note", "priority"}
    WAREHOUSE_EDITABLE_FIELDS = {
        "assignee",
        "internal_note",
        "track_number",
        "priority",
    }
    WAREHOUSE_ACTIONS = {
        "mark_picking",
        "mark_packed",
        "mark_shipped",
    }
    ORDER_MANAGER_ACTIONS = {
        "create_shipment",
        "refresh_tracking",
        "mark_picking",
        "mark_packed",
        "mark_shipped",
        "mark_delivered",
        "mark_cancelled",
        "mark_returned",
    }

    list_display = (
        "id",
        "user",
        "status",
        "priority_badge",
        "assignee",
        "payment_status_badge",
        "delivery_status_badge",
        "fulfillment_next_step",
        "total_amount",
        "track_number",
        "created_at",
    )
    list_filter = (
        "status",
        "priority",
        "assignee",
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
    readonly_fields = ("total_amount", "packing_slip_link")
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
    fieldsets = (
        (
            "Операционный контур",
            {
                "fields": (
                    "status",
                    "priority",
                    "assignee",
                    "internal_note",
                    "packing_slip_link",
                )
            },
        ),
        (
            "Доставка клиента",
            {
                "fields": (
                    "total_amount",
                    "track_number",
                    "shipping_name",
                    "shipping_phone",
                    "shipping_country",
                    "shipping_city",
                    "shipping_postal_code",
                    "shipping_line1",
                    "shipping_line2",
                )
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "delivery_snapshot").prefetch_related(
            "payments", "items"
        )

    def _can_manage_orders(self, user):
        return user_has_staff_role(
            user,
            ROLE_OWNER,
            ROLE_ORDER_MANAGER,
            ROLE_WAREHOUSE_OPERATOR,
            ROLE_SUPPORT_AGENT,
        )

    def _is_order_manager(self, user):
        return user_has_staff_role(user, ROLE_OWNER, ROLE_ORDER_MANAGER)

    def _is_warehouse(self, user):
        return user_has_staff_role(user, ROLE_OWNER, ROLE_WAREHOUSE_OPERATOR)

    def _is_support(self, user):
        return user_has_staff_role(user, ROLE_OWNER, ROLE_SUPPORT_AGENT)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return self._can_manage_orders(request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self._can_manage_orders(request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self._can_manage_orders(request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if request.user.is_superuser or self._is_order_manager(request.user):
            return readonly

        local_field_names = [field.name for field in self.model._meta.fields]
        editable = set()
        if self._is_support(request.user):
            editable = self.SUPPORT_EDITABLE_FIELDS
        elif self._is_warehouse(request.user):
            editable = self.WAREHOUSE_EDITABLE_FIELDS

        readonly.extend(
            field_name
            for field_name in local_field_names
            if field_name not in editable and field_name not in readonly
        )
        return readonly

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            return actions
        if self._is_order_manager(request.user):
            return {
                name: action
                for name, action in actions.items()
                if name in self.ORDER_MANAGER_ACTIONS
            }
        if self._is_warehouse(request.user):
            return {
                name: action
                for name, action in actions.items()
                if name in self.WAREHOUSE_ACTIONS
            }
        return {}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:order_id>/packing-slip/",
                self.admin_site.admin_view(self.packing_slip_view),
                name="orders_order_packing_slip",
            )
        ]
        return custom_urls + urls

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

    @admin.display(description="Приоритет")
    def priority_badge(self, obj):
        palette = {
            Order.Priority.NORMAL: ("#334155", "#f8fafc"),
            Order.Priority.HIGH: ("#b45309", "#fffbeb"),
            Order.Priority.URGENT: ("#991b1b", "#fef2f2"),
        }
        background, color = palette.get(obj.priority, ("#334155", "#f8fafc"))
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;'
            'background:{};color:{};">{}</span>',
            background,
            color,
            obj.get_priority_display(),
        )

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

    @admin.display(description="Packing slip")
    def packing_slip_link(self, obj):
        if not obj or not obj.pk:
            return "Сохраните заказ, чтобы открыть packing slip."
        url = reverse("admin:orders_order_packing_slip", args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Открыть packing slip</a>', url)

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
            "urgent_orders": queryset.filter(priority=Order.Priority.URGENT).count(),
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

    def packing_slip_view(self, request, order_id):
        order = (
            self.get_queryset(request)
            .filter(pk=order_id)
            .select_related("assignee")
            .first()
        )
        if order is None:
            raise Http404("Order not found.")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": order,
            "title": f"Packing slip for order #{order.id}",
            "order": order,
            "snapshot": self._get_delivery_snapshot(order),
            "items": list(order.items.all()),
        }
        return TemplateResponse(
            request,
            "admin/orders/order/packing_slip.html",
            context,
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
