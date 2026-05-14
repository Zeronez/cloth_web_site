from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_address_users_addr_user_def_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
