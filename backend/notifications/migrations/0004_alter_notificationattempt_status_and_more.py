from django.db import migrations, models


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
