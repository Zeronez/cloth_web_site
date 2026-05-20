from django.db import migrations, models


def approve_existing_product_images(apps, schema_editor):
    ProductImage = apps.get_model("catalog", "ProductImage")
    ProductImage.objects.filter(is_approved=False).update(is_approved=True)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_product_currency_product_sale_ends_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="productimage",
            name="is_approved",
            field=models.BooleanField(
                default=True,
                help_text="If disabled, the image will not be exposed on public storefront APIs.",
            ),
        ),
        migrations.RunPython(
            approve_existing_product_images, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="productimage",
            name="is_approved",
            field=models.BooleanField(
                default=False,
                help_text="If disabled, the image will not be exposed on public storefront APIs.",
            ),
        ),
    ]
