from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_notificationattempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationlog",
            name="dead_lettered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
