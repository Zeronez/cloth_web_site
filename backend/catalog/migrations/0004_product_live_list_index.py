from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_product_archived_at"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_active", "archived_at", "is_featured", "created_at"],
                name="catalog_pro_live_list_idx",
            ),
        ),
    ]
