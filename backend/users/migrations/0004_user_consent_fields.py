from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_email_verified_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="marketing_opt_in_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="marketing_opt_in_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="offer_agreement_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="offer_agreement_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="privacy_policy_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="privacy_policy_version",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
