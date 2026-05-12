from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_product_live_list_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariant",
            name="stock_version",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
