from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("favorites", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="favoriteproduct",
            index=models.Index(
                fields=["user", "created_at"],
                name="favorites_user_created_idx",
            ),
        ),
    ]
