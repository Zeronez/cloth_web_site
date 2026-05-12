from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0003_alter_paymentmethod_session_mode"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="paymentmethod",
            index=models.Index(
                fields=["provider_code", "session_mode"],
                name="payments_me_prov_mode_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["user", "created_at"],
                name="payments_pa_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["order", "provider_code", "external_payment_id"],
                name="payments_pa_ordprovext_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["provider_code", "status"],
                name="payments_pa_prov_stat_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["method_code"],
                name="payments_pa_method_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["status", "created_at"],
                name="payments_pa_status_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["session_expires_at"],
                name="payments_pa_expire_idx",
            ),
        ),
    ]
