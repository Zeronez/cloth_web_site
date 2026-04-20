import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
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
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("shipped", "Shipped"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=24,
                    ),
                ),
                ("track_number", models.CharField(blank=True, max_length=120)),
                ("shipping_name", models.CharField(max_length=160)),
                ("shipping_phone", models.CharField(max_length=32)),
                ("shipping_country", models.CharField(max_length=80)),
                ("shipping_city", models.CharField(max_length=120)),
                ("shipping_postal_code", models.CharField(max_length=32)),
                ("shipping_line1", models.CharField(max_length=255)),
                ("shipping_line2", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
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
                ("product_name", models.CharField(max_length=180)),
                ("sku", models.CharField(max_length=64)),
                ("size", models.CharField(max_length=16)),
                ("color", models.CharField(max_length=80)),
                ("quantity", models.PositiveIntegerField()),
                (
                    "price_at_purchase",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="catalog.productvariant",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["user", "status"], name="orders_orde_user_id_f64abd_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["created_at"], name="orders_orde_created_0fc1c0_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["sku"], name="orders_orde_sku_71777a_idx"),
        ),
    ]
