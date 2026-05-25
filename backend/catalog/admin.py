from decimal import Decimal, ROUND_HALF_UP

from django.contrib import admin, messages

from audit.admin_mixins import AuditedModelAdminMixin
from audit.models import AuditLog
from audit.services import log_admin_event, model_snapshot
from catalog.models import (
    AnimeFranchise,
    Category,
    InventoryAdjustment,
    LowStockAlert,
    Product,
    ProductCollection,
    RecommendationDecisionLog,
    ProductImage,
    ProductTag,
    ProductVariant,
    ProductVideo,
    SizeChart,
)
from catalog.stock import LOW_STOCK_THRESHOLD, adjust_variant_stock, is_low_stock
from config.admin_exports import export_as_csv
from users.staff_roles import (
    ROLE_CATALOG_MANAGER,
    ROLE_INVENTORY_MANAGER,
    ROLE_OWNER,
    user_has_staff_role,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = (
        "sku",
        "size",
        "color",
        "stock_quantity",
        "price_delta",
        "recommendation_fit_tendency_override",
        "recommendation_notes_override",
        "is_active",
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("variant", "image", "alt_text", "is_main", "is_approved", "sort_order")


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0
    fields = ("variant", "url", "alt_text", "sort_order")


class LowStockListFilter(admin.SimpleListFilter):
    title = "низкий остаток"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Нужно пополнение"),
            ("no", "Остаток в норме"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD)
        if self.value() == "no":
            return queryset.filter(stock_quantity__gt=LOW_STOCK_THRESHOLD)
        return queryset


class InventoryAdjustmentInline(admin.TabularInline):
    model = InventoryAdjustment
    extra = 0
    can_delete = False
    fields = (
        "created_at",
        "performed_by",
        "reason",
        "delta",
        "previous_quantity",
        "new_quantity",
        "note",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active", "created_at", "updated_at")
    date_hierarchy = "created_at"
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AnimeFranchise)
class AnimeFranchiseAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active", "created_at", "updated_at")
    date_hierarchy = "created_at"
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Product)
class ProductAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    PRICE_QUANT = Decimal("0.01")
    excluded_fields = (
        "collections",
        "search_synonyms",
        "material",
        "fit",
        "care",
        "gender",
        "season",
        "weight_grams",
        "seo_title",
        "seo_description",
    )

    list_display = (
        "name",
        "category",
        "franchise",
        "base_price",
        "recommendation_fit_tendency",
        "status",
        "is_active",
        "is_featured",
        "archived_at",
    )
    list_filter = (
        "status",
        "is_active",
        "is_featured",
        "archived_at",
        "category",
        "franchise",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    list_select_related = ("category", "franchise")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "variants__sku")
    inlines = [ProductVariantInline, ProductImageInline]
    exclude = excluded_fields
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "franchise",
                    "name",
                    "slug",
                    "description",
                    "base_price",
                    "currency",
                    "sale_price",
                    "sale_starts_at",
                    "sale_ends_at",
                    "status",
                    "is_featured",
                    "canonical_url",
                    "og_image_url",
                    "tags",
                )
            },
        ),
        (
            "Recommendation metadata",
            {
                "fields": (
                    "recommendation_fit_tendency",
                    "recommendation_fit_confidence",
                    "recommendation_silhouette",
                    "recommendation_style_tags",
                    "recommendation_seasonality",
                    "recommendation_layering_role",
                    "recommendation_body_shape_notes",
                    "recommendation_notes",
                ),
                "description": "Данные для умной примерочной, капсульных образов и объяснений рекомендаций.",
            },
        ),
    )
    actions = (
        "archive_selected_products",
        "restore_selected_products",
        "activate_selected_products",
        "deactivate_selected_products",
        "feature_selected_products",
        "unfeature_selected_products",
        "increase_selected_product_prices_10_percent",
        "decrease_selected_product_prices_10_percent",
    )

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def _bulk_set_boolean(self, request, queryset, *, field_name, value, action_name):
        selected_count = queryset.count()
        updated = 0
        for product in queryset:
            old_value = getattr(product, field_name)
            if old_value == value:
                continue
            setattr(product, field_name, value)
            product.save(update_fields=[field_name, "updated_at"])
            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=product,
                request=request,
                changes={field_name: {"old": old_value, "new": value}},
                metadata={
                    "admin_action": action_name,
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "product_id": product.id,
                    "slug": product.slug,
                },
            )
        self.message_user(request, f"Обновлено товаров: {updated}.", messages.SUCCESS)

    def _bulk_adjust_price(self, request, queryset, *, multiplier, action_name):
        selected_count = queryset.count()
        updated = 0
        for product in queryset:
            old_price = product.base_price
            new_price = (old_price * multiplier).quantize(
                self.PRICE_QUANT,
                rounding=ROUND_HALF_UP,
            )
            if new_price == old_price:
                continue
            product.base_price = new_price
            product.save(update_fields=["base_price", "updated_at"])
            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=product,
                request=request,
                changes={"base_price": {"old": str(old_price), "new": str(new_price)}},
                metadata={
                    "admin_action": action_name,
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "product_id": product.id,
                    "slug": product.slug,
                    "multiplier": str(multiplier),
                },
            )
        self.message_user(
            request, f"Обновлено цен товаров: {updated}.", messages.SUCCESS
        )

    @admin.action(description="Опубликовать выбранные товары")
    def _bulk_archive_products(self, request, queryset, *, archived, action_name):
        selected_count = queryset.count()
        updated = 0
        for product in queryset:
            old_archived_at = (
                product.archived_at.isoformat() if product.archived_at else None
            )
            old_is_active = product.is_active
            old_is_featured = product.is_featured

            if archived:
                if product.is_archived:
                    continue
                product.archive()
            else:
                if not product.is_archived:
                    continue
                product.restore()

            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=product,
                request=request,
                changes={
                    "archived_at": {
                        "old": old_archived_at,
                        "new": (
                            product.archived_at.isoformat()
                            if product.archived_at
                            else None
                        ),
                    },
                    "is_active": {"old": old_is_active, "new": product.is_active},
                    "is_featured": {
                        "old": old_is_featured,
                        "new": product.is_featured,
                    },
                },
                metadata={
                    "admin_action": action_name,
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "product_id": product.id,
                    "slug": product.slug,
                },
            )
        self.message_user(
            request,
            f"Archived products updated: {updated}.",
            messages.SUCCESS,
        )

    @admin.action(description="Archive selected products")
    def archive_selected_products(self, request, queryset):
        self._bulk_archive_products(
            request,
            queryset,
            archived=True,
            action_name="archive_selected_products",
        )

    @admin.action(description="Restore selected products from archive")
    def restore_selected_products(self, request, queryset):
        self._bulk_archive_products(
            request,
            queryset,
            archived=False,
            action_name="restore_selected_products",
        )

    def activate_selected_products(self, request, queryset):
        self._bulk_set_boolean(
            request,
            queryset.filter(archived_at__isnull=True),
            field_name="is_active",
            value=True,
            action_name="activate_selected_products",
        )

    @admin.action(description="Снять выбранные товары с публикации")
    def deactivate_selected_products(self, request, queryset):
        self._bulk_set_boolean(
            request,
            queryset,
            field_name="is_active",
            value=False,
            action_name="deactivate_selected_products",
        )

    @admin.action(description="Добавить выбранные товары в избранное")
    def feature_selected_products(self, request, queryset):
        self._bulk_set_boolean(
            request,
            queryset,
            field_name="is_featured",
            value=True,
            action_name="feature_selected_products",
        )

    @admin.action(description="Убрать выбранные товары из избранного")
    def unfeature_selected_products(self, request, queryset):
        self._bulk_set_boolean(
            request,
            queryset,
            field_name="is_featured",
            value=False,
            action_name="unfeature_selected_products",
        )

    @admin.action(description="Поднять базовую цену выбранных товаров на 10%%")
    def increase_selected_product_prices_10_percent(self, request, queryset):
        self._bulk_adjust_price(
            request,
            queryset,
            multiplier=Decimal("1.10"),
            action_name="increase_selected_product_prices_10_percent",
        )

    @admin.action(description="Снизить базовую цену выбранных товаров на 10%%")
    def decrease_selected_product_prices_10_percent(self, request, queryset):
        self._bulk_adjust_price(
            request,
            queryset,
            multiplier=Decimal("0.90"),
            action_name="decrease_selected_product_prices_10_percent",
        )


@admin.register(ProductVariant)
class ProductVariantAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "size",
        "color",
        "stock_badge",
        "is_active",
    )
    list_filter = (
        "is_active",
        "size",
        "color",
        "product__category",
        "product__franchise",
        LowStockListFilter,
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    list_select_related = ("product", "product__category", "product__franchise")
    search_fields = ("sku", "product__name", "color")
    inlines = [InventoryAdjustmentInline]
    actions = (
        "activate_selected_variants",
        "deactivate_selected_variants",
        "mark_zero_stock_variants_inactive",
        "restock_selected_variants_by_1",
        "restock_selected_variants_by_5",
        "write_off_selected_variants_by_1",
        "set_selected_variants_price_delta_zero",
        "export_sku_stock_csv",
    )

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(
            request.user,
            ROLE_OWNER,
            ROLE_CATALOG_MANAGER,
            ROLE_INVENTORY_MANAGER,
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or user_has_staff_role(
            request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER
        ):
            return ()
        return (
            "product",
            "sku",
            "size",
            "color",
            "stock_quantity",
            "price_delta",
            "is_active",
        )

    @admin.display(description="Остаток")
    def stock_badge(self, obj):
        if is_low_stock(obj):
            return f"{obj.stock_quantity} · low"
        return str(obj.stock_quantity)

    def _bulk_set_variant_active(self, request, queryset, *, value, action_name):
        selected_count = queryset.count()
        updated = 0
        for variant in queryset.select_related("product"):
            old_value = variant.is_active
            if old_value == value:
                continue
            variant.is_active = value
            variant.save(update_fields=["is_active", "updated_at"])
            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=variant,
                request=request,
                changes={"is_active": {"old": old_value, "new": value}},
                metadata={
                    "admin_action": action_name,
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "variant_id": variant.id,
                    "sku": variant.sku,
                },
            )
        self.message_user(request, f"Обновлено SKU: {updated}.", messages.SUCCESS)

    def _bulk_adjust_variant_stock(
        self, request, queryset, *, delta, reason, action_name
    ):
        selected_count = queryset.count()
        updated = 0
        skipped = 0
        for variant in queryset.select_related("product"):
            if variant.stock_quantity + delta < 0:
                skipped += 1
                continue
            _variant, adjustment = adjust_variant_stock(
                variant_id=variant.id,
                delta=delta,
                reason=reason,
                performed_by=request.user,
                note=f"Массовое admin-действие {action_name} для SKU {variant.sku}.",
            )
            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=adjustment,
                request=request,
                snapshot=model_snapshot(
                    adjustment,
                    (
                        "variant_id",
                        "reason",
                        "delta",
                        "previous_quantity",
                        "new_quantity",
                        "performed_by_id",
                        "note",
                    ),
                ),
                metadata={
                    "admin_action": action_name,
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "skipped_count": skipped,
                    "variant_id": variant.id,
                    "sku": variant.sku,
                    "delta": delta,
                    "reason": reason,
                    "adjustment_id": adjustment.id,
                },
            )
        if skipped:
            self.message_user(
                request,
                f"Пропущено SKU без достаточного остатка: {skipped}.",
                messages.WARNING,
            )
        self.message_user(
            request, f"Обновлено остатков SKU: {updated}.", messages.SUCCESS
        )

    @admin.action(description="Активировать выбранные SKU")
    def activate_selected_variants(self, request, queryset):
        self._bulk_set_variant_active(
            request,
            queryset,
            value=True,
            action_name="activate_selected_variants",
        )

    @admin.action(description="Деактивировать выбранные SKU")
    def deactivate_selected_variants(self, request, queryset):
        self._bulk_set_variant_active(
            request,
            queryset,
            value=False,
            action_name="deactivate_selected_variants",
        )

    @admin.action(description="Деактивировать выбранные SKU с нулевым остатком")
    def mark_zero_stock_variants_inactive(self, request, queryset):
        self._bulk_set_variant_active(
            request,
            queryset.filter(stock_quantity=0),
            value=False,
            action_name="mark_zero_stock_variants_inactive",
        )

    @admin.action(description="Пополнить выбранные SKU на 1 единицу")
    def restock_selected_variants_by_1(self, request, queryset):
        self._bulk_adjust_variant_stock(
            request,
            queryset,
            delta=1,
            reason=InventoryAdjustment.Reason.RESTOCK,
            action_name="restock_selected_variants_by_1",
        )

    @admin.action(description="Пополнить выбранные SKU на 5 единиц")
    def restock_selected_variants_by_5(self, request, queryset):
        self._bulk_adjust_variant_stock(
            request,
            queryset,
            delta=5,
            reason=InventoryAdjustment.Reason.RESTOCK,
            action_name="restock_selected_variants_by_5",
        )

    @admin.action(description="Списать 1 единицу у выбранных SKU")
    def write_off_selected_variants_by_1(self, request, queryset):
        self._bulk_adjust_variant_stock(
            request,
            queryset,
            delta=-1,
            reason=InventoryAdjustment.Reason.DAMAGE,
            action_name="write_off_selected_variants_by_1",
        )

    @admin.action(description="Обнулить price_delta у выбранных SKU")
    def set_selected_variants_price_delta_zero(self, request, queryset):
        selected_count = queryset.count()
        updated = 0
        for variant in queryset.select_related("product"):
            old_value = variant.price_delta
            if old_value == 0:
                continue
            variant.price_delta = Decimal("0.00")
            variant.save(update_fields=["price_delta", "updated_at"])
            updated += 1
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=variant,
                request=request,
                changes={
                    "price_delta": {
                        "old": str(old_value),
                        "new": "0.00",
                    }
                },
                metadata={
                    "admin_action": "set_selected_variants_price_delta_zero",
                    "selected_count": selected_count,
                    "changed_count": updated,
                    "variant_id": variant.id,
                    "sku": variant.sku,
                },
            )
        self.message_user(request, f"Обновлено SKU: {updated}.", messages.SUCCESS)

    @admin.action(description="Экспортировать выбранные SKU-остатки в CSV")
    def export_sku_stock_csv(self, request, queryset):
        rows = []
        queryset = queryset.select_related("product", "product__category")
        selected_count = queryset.count()
        for variant in queryset:
            rows.append(
                [
                    variant.sku,
                    variant.product.name,
                    variant.product.category.name,
                    variant.size,
                    variant.color,
                    variant.stock_quantity,
                    "yes" if is_low_stock(variant) else "no",
                    variant.is_active,
                    variant.price,
                ]
            )
            log_admin_event(
                actor=request.user,
                action=AuditLog.Action.ADMIN_ACTION,
                obj=variant,
                request=request,
                metadata={
                    "admin_action": "export_sku_stock_csv",
                    "selected_count": selected_count,
                    "sku": variant.sku,
                },
            )
        return export_as_csv(
            filename="animeattire-sku-stock.csv",
            headers=[
                "sku",
                "product_name",
                "category",
                "size",
                "color",
                "stock_quantity",
                "low_stock",
                "is_active",
                "price",
            ],
            rows=rows,
        )


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "reason",
        "delta",
        "previous_quantity",
        "new_quantity",
        "performed_by",
        "created_at",
    )
    list_filter = ("reason", "created_at")
    list_select_related = ("variant", "variant__product", "performed_by")
    search_fields = ("variant__sku", "variant__product__name", "note")
    fields = ("variant", "reason", "delta", "note")
    readonly_fields = (
        "performed_by",
        "previous_quantity",
        "new_quantity",
        "created_at",
        "updated_at",
    )

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_INVENTORY_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return
        variant, adjustment = adjust_variant_stock(
            variant_id=obj.variant_id,
            delta=obj.delta,
            reason=obj.reason,
            performed_by=request.user,
            note=obj.note,
        )
        obj.pk = adjustment.pk
        obj.variant = variant
        obj.performed_by = adjustment.performed_by
        obj.previous_quantity = adjustment.previous_quantity
        obj.new_quantity = adjustment.new_quantity
        obj.created_at = adjustment.created_at
        obj.updated_at = adjustment.updated_at
        self.message_user(
            request,
            f"Остаток {variant.sku} обновлён: {adjustment.previous_quantity} -> {adjustment.new_quantity}.",
            level=messages.SUCCESS,
        )
        log_admin_event(
            actor=request.user,
            action=AuditLog.Action.ADMIN_ACTION,
            obj=adjustment,
            request=request,
            snapshot=model_snapshot(
                adjustment,
                (
                    "variant_id",
                    "reason",
                    "delta",
                    "previous_quantity",
                    "new_quantity",
                    "performed_by_id",
                    "note",
                ),
            ),
            metadata={
                "admin_action": "inventory_adjustment_add",
                "variant_id": variant.id,
                "sku": variant.sku,
            },
        )


@admin.register(ProductImage)
class ProductImageAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("alt_text", "product", "is_main", "is_approved", "sort_order")
    list_filter = ("is_main", "is_approved")
    list_select_related = ("product",)
    search_fields = ("alt_text", "product__name")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return user_has_staff_role(request.user, ROLE_OWNER, ROLE_CATALOG_MANAGER)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductTag)
class ProductTagAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductCollection)
class ProductCollectionAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "starts_at", "ends_at")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SizeChart)
class SizeChartAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = ("id", "title", "category", "product", "created_at")
    list_filter = ("category", "product")
    search_fields = ("title",)


@admin.register(LowStockAlert)
class LowStockAlertAdmin(AuditedModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "variant",
        "stock_quantity",
        "threshold",
        "acknowledged_at",
        "created_at",
    )
    list_filter = ("acknowledged_at", "created_at")
    search_fields = ("variant__sku", "variant__product__name")


@admin.register(RecommendationDecisionLog)
class RecommendationDecisionLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "source",
        "product",
        "user",
        "recommended_size",
        "confidence",
        "risk_level",
    )
    list_filter = ("source", "confidence", "risk_level", "created_at")
    search_fields = ("product__name", "product__slug", "user__username", "user__email")
    readonly_fields = (
        "created_at",
        "updated_at",
        "product",
        "user",
        "source",
        "recommended_size",
        "confidence",
        "risk_level",
        "warnings",
        "reasons",
        "fallback_action",
        "profile_snapshot",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
