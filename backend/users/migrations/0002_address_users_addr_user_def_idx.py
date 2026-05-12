from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="address",
            index=models.Index(
                fields=["user", "is_default", "created_at"],
                name="users_addr_user_def_idx",
            ),
        ),
    ]
