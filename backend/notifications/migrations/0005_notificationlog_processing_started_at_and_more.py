from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0004_alter_notificationattempt_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationlog",
            name="processing_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="notificationlog",
            index=models.Index(
                fields=["dead_lettered_at"],
                name="notif_log_dead_letter_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notificationlog",
            index=models.Index(
                fields=["processing_started_at"],
                name="notif_log_processing_idx",
            ),
        ),
    ]
