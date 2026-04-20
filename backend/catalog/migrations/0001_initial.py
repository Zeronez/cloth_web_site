import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AnimeFranchise",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=180, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=180)),
                ("slug", models.SlugField(blank=True, max_length=200, unique=True)),
                ("description", models.TextField()),
                ("base_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
                (
                    "franchise",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.animefranchise",
                    ),
                ),
            ],
            options={"ordering": ["-is_featured", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(upload_to="products/")),
                ("alt_text", models.CharField(max_length=180)),
                ("is_main", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sku", models.CharField(max_length=64, unique=True)),
                (
                    "size",
                    models.CharField(
                        choices=[
                            ("XS", "XS"),
                            ("S", "S"),
                            ("M", "M"),
                            ("L", "L"),
                            ("XL", "XL"),
                            ("XXL", "XXL"),
                            ("ONE_SIZE", "One size"),
                        ],
                        max_length=16,
                    ),
                ),
                ("color", models.CharField(max_length=80)),
                ("stock_quantity", models.PositiveIntegerField(default=0)),
                (
                    "price_delta",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["product", "color", "size"]},
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="catalog_pro_slug_13a17c_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_active", "is_featured"],
                name="catalog_pro_is_acti_c4e01c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="productimage",
            index=models.Index(
                fields=["product", "is_main"], name="catalog_pro_product_292fff_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(fields=["sku"], name="catalog_pro_sku_e76e0b_idx"),
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(
                fields=["is_active", "stock_quantity"],
                name="catalog_pro_is_acti_36416c_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="productvariant",
            constraint=models.UniqueConstraint(
                fields=("product", "size", "color"), name="unique_product_size_color"
            ),
        ),
    ]
