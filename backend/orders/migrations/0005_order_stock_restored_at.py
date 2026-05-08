from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_order_assignee_order_internal_note_order_priority"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stock_restored_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
