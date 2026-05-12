from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("delivery", "0003_alter_deliverytrackingevent_new_status_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="orderdeliverysnapshot",
            index=models.Index(
                fields=["method_kind"],
                name="delivery_or_kind_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="orderdeliverysnapshot",
            index=models.Index(
                fields=["provider_code", "tracking_status"],
                name="delivery_or_prov_stat_idx",
            ),
        ),
    ]
