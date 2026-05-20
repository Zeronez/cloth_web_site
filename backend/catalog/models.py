from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from config.uploads import validate_product_image_upload


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AnimeFranchise(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    class PublishingStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT
    )
    franchise = models.ForeignKey(
        AnimeFranchise,
        related_name="products",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(
        max_length=16,
        choices=PublishingStatus.choices,
        default=PublishingStatus.ACTIVE,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    tags = models.ManyToManyField(
        "catalog.ProductTag",
        blank=True,
        related_name="products",
    )
    collections = models.ManyToManyField(
        "catalog.ProductCollection", blank=True, related_name="products"
    )

    search_synonyms = models.TextField(blank=True)

    material = models.CharField(max_length=120, blank=True)
    fit = models.CharField(max_length=120, blank=True)
    care = models.TextField(blank=True)
    gender = models.CharField(max_length=32, blank=True)
    season = models.CharField(max_length=32, blank=True)
    weight_grams = models.PositiveIntegerField(null=True, blank=True)

    seo_title = models.CharField(max_length=180, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
    canonical_url = models.URLField(blank=True)
    og_image_url = models.URLField(blank=True)

    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    sale_starts_at = models.DateTimeField(null=True, blank=True)
    sale_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["slug"], name="catalog_pro_slug_13a17c_idx"),
            models.Index(
                fields=["is_active", "is_featured"],
                name="catalog_pro_is_acti_c4e01c_idx",
            ),
            models.Index(
                fields=["archived_at"],
                name="catalog_pro_arch_at_idx",
            ),
            models.Index(
                fields=["is_active", "archived_at", "is_featured", "created_at"],
                name="catalog_pro_live_list_idx",
            ),
            models.Index(fields=["status", "created_at"], name="catalog_pro_status_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.archived_at is not None and self.status != self.PublishingStatus.ARCHIVED:
            self.status = self.PublishingStatus.ARCHIVED
        elif self.status == self.PublishingStatus.ACTIVE and not self.is_active:
            self.status = self.PublishingStatus.DRAFT
        elif self.status == self.PublishingStatus.DRAFT and self.is_active:
            self.status = self.PublishingStatus.ACTIVE

        if self.status == self.PublishingStatus.ARCHIVED:
            if self.archived_at is None:
                self.archived_at = timezone.now()
            self.is_active = False
            self.is_featured = False
        elif self.status == self.PublishingStatus.DRAFT:
            self.archived_at = None
            self.is_active = False
            self.is_featured = False
        else:
            self.archived_at = None
            self.is_active = True
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def total_stock(self):
        return sum(
            variant.stock_quantity
            for variant in self.variants.all()
            if variant.is_active
        )

    @property
    def is_archived(self):
        return self.archived_at is not None

    def archive(self, *, save=True):
        self.status = self.PublishingStatus.ARCHIVED
        if save:
            self.save(
                update_fields=[
                    "status",
                    "archived_at",
                    "is_active",
                    "is_featured",
                    "updated_at",
                ]
            )
        self.variants.filter(is_active=True).update(
            is_active=False, updated_at=timezone.now()
        )

    def restore(self, *, save=True):
        self.status = self.PublishingStatus.ACTIVE
        if save:
            self.save(update_fields=["status", "archived_at", "is_active", "updated_at"])

    def __str__(self):
        return self.name


class ProductCollection(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductTag(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SizeChart(TimeStampedModel):
    category = models.ForeignKey(
        Category,
        related_name="size_charts",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="size_charts",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=160, default="Size chart")
    measurements = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["category"], name="catalog_size_chart_cat_idx"),
            models.Index(fields=["product"], name="catalog_size_chart_prod_idx"),
        ]

    def __str__(self):
        scope = "product" if self.product_id else "category"
        return f"{scope} size chart #{self.id}"


class ProductRelation(TimeStampedModel):
    from_product = models.ForeignKey(
        Product, related_name="related_from", on_delete=models.CASCADE
    )
    to_product = models.ForeignKey(
        Product, related_name="related_to", on_delete=models.CASCADE
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_product", "to_product"],
                name="catalog_unique_product_relation",
            )
        ]
        indexes = [
            models.Index(fields=["from_product"], name="catalog_rel_from_idx"),
            models.Index(fields=["to_product"], name="catalog_rel_to_idx"),
        ]

    def __str__(self):
        return f"{self.from_product_id} -> {self.to_product_id}"


class ProductVariant(TimeStampedModel):
    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        ONE_SIZE = "ONE_SIZE", "One size"

    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    sku = models.CharField(max_length=64, unique=True)
    size = models.CharField(max_length=16, choices=Size.choices)
    color = models.CharField(max_length=80)
    stock_quantity = models.PositiveIntegerField(default=0)
    stock_version = models.PositiveIntegerField(default=0)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product", "color", "size"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "size", "color"],
                name="unique_product_size_color",
            )
        ]
        indexes = [
            models.Index(fields=["sku"], name="catalog_pro_sku_e76e0b_idx"),
            models.Index(
                fields=["is_active", "stock_quantity"],
                name="catalog_pro_is_acti_36416c_idx",
            ),
        ]

    @property
    def price(self):
        base_price = self.product.base_price
        sale_price = getattr(self.product, "sale_price", None)
        if sale_price is not None:
            now = timezone.now()
            starts = getattr(self.product, "sale_starts_at", None)
            ends = getattr(self.product, "sale_ends_at", None)
            if (starts is None or now >= starts) and (ends is None or now < ends):
                base_price = sale_price
        return base_price + self.price_delta

    def __str__(self):
        return f"{self.product.name} / {self.color} / {self.size}"


class InventoryReservation(TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        related_name="reservations",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "users.User",
        related_name="inventory_reservations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    order = models.ForeignKey(
        "orders.Order",
        related_name="inventory_reservations",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["variant", "expires_at"],
                name="catalog_res_var_exp_idx",
            ),
            models.Index(fields=["expires_at"], name="catalog_res_exp_idx"),
            models.Index(fields=["released_at"], name="catalog_res_rel_idx"),
        ]

    @property
    def is_active(self):
        return self.released_at is None and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reservation {self.variant_id} x{self.quantity}"


class InventoryAdjustment(TimeStampedModel):
    class Reason(models.TextChoices):
        RESTOCK = "restock", "Пополнение"
        COUNT = "count", "Инвентаризация"
        DAMAGE = "damage", "Списание брака"
        RETURN = "return", "Возврат на склад"
        MANUAL = "manual", "Ручная корректировка"

    variant = models.ForeignKey(
        ProductVariant,
        related_name="inventory_adjustments",
        on_delete=models.PROTECT,
    )
    performed_by = models.ForeignKey(
        "users.User",
        related_name="inventory_adjustments",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reason = models.CharField(max_length=24, choices=Reason.choices)
    delta = models.IntegerField()
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["variant", "created_at"],
                name="catalog_inv_variant_a5f6d3_idx",
            ),
            models.Index(fields=["reason"], name="catalog_inv_reason_3db8dd_idx"),
        ]

    def __str__(self):
        return f"{self.variant.sku}: {self.delta:+d} -> {self.new_quantity}"


class LowStockAlert(TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        related_name="low_stock_alerts",
        on_delete=models.CASCADE,
    )
    threshold = models.PositiveIntegerField(default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        "users.User",
        related_name="acknowledged_low_stock_alerts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["variant", "created_at"], name="catalog_low_stock_var_idx"),
            models.Index(fields=["acknowledged_at"], name="catalog_low_stock_ack_idx"),
        ]

    @property
    def is_acknowledged(self):
        return self.acknowledged_at is not None

    def __str__(self):
        return f"Low stock {self.variant.sku} ({self.stock_quantity})"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        ProductVariant,
        related_name="images",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=180)
    is_main = models.BooleanField(default=False)
    is_approved = models.BooleanField(
        default=False,
        help_text="If disabled, the image will not be exposed on public storefront APIs.",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(
                fields=["product", "is_main"],
                name="catalog_pro_product_292fff_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if self.image and not getattr(self.image, "_committed", True):
            validate_product_image_upload(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.alt_text


class ProductVideo(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="videos", on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        ProductVariant,
        related_name="videos",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    url = models.URLField()
    alt_text = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["product"], name="catalog_video_product_idx"),
            models.Index(fields=["variant"], name="catalog_video_variant_idx"),
        ]

    def __str__(self):
        return self.url


class ProductPriceHistory(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="price_history", on_delete=models.CASCADE
    )
    changed_by = models.ForeignKey(
        "users.User",
        related_name="product_price_changes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    field_name = models.CharField(max_length=32)
    old_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["product", "created_at"], name="catalog_price_hist_prod_idx"),
            models.Index(fields=["field_name"], name="catalog_price_hist_field_idx"),
        ]

    def __str__(self):
        return f"{self.product_id} {self.field_name}: {self.old_value} -> {self.new_value}"
