from django.db import migrations, models


MIGRATION_SAFETY_PLAN = {
    "ticket": "OPS-142",
    "summary": "Expand notification status choices for retry scheduling and dead-letter handling.",
    "backfill": "No data backfill is required because the migration only widens allowed enum-style choices for existing text fields.",
    "deploy_strategy": "Deploy application code that understands the new statuses together with this migration in one release.",
    "rollback": "Rollback application code first, then restore the previous migration state if new statuses were not written or are remapped.",
}


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0003_notificationlog_dead_lettered_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationattempt",
            name="status",
            field=models.CharField(
                choices=[
                    ("delivered", "Доставлено"),
                    ("failed", "Ошибка"),
                    ("retry_scheduled", "Повтор запланирован"),
                ],
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="notificationlog",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает отправки"),
                    ("delivered", "Доставлено"),
                    ("failed", "Ошибка"),
                    ("dead_lettered", "Требует вмешательства"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
    ]
