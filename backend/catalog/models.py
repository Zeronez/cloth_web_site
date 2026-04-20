from django.db import models
from django.utils.text import slugify


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
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["slug"], name="catalog_pro_slug_13a17c_idx"),
            models.Index(
                fields=["is_active", "is_featured"],
                name="catalog_pro_is_acti_c4e01c_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def total_stock(self):
        return sum(variant.stock_quantity for variant in self.variants.all())

    def __str__(self):
        return self.name


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
        return self.product.base_price + self.price_delta

    def __str__(self):
        return f"{self.product.name} / {self.color} / {self.size}"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=180)
    is_main = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(
                fields=["product", "is_main"],
                name="catalog_pro_product_292fff_idx",
            )
        ]

    def __str__(self):
        return self.alt_text
