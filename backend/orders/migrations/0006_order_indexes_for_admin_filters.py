from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_order_stock_restored_at"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["priority"],
                name="orders_priority_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["stock_restored_at"],
                name="orders_stock_restored_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["status", "created_at"],
                name="orders_status_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["user", "created_at"],
                name="orders_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["shipping_country", "shipping_city"],
                name="orders_ship_country_city_idx",
            ),
        ),
    ]
