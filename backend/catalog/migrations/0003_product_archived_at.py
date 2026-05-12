from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_inventoryadjustment"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["archived_at"],
                name="catalog_pro_arch_at_idx",
            ),
        ),
    ]
