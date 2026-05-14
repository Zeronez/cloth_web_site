from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_consent_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="account_deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
