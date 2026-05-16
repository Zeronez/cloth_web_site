from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from catalog.models import ProductImage


pytestmark = pytest.mark.django_db


def make_test_image():
    buffer = BytesIO()
    Image.new("RGB", (12, 12), color=(20, 40, 220)).save(buffer, format="PNG")
    return SimpleUploadedFile(
        "storage-tee.png",
        buffer.getvalue(),
        content_type="image/png",
    )


def test_product_images_persist_through_configured_storage_and_product_api(
    api_client, product_factory
):
    product = product_factory(name="Storage Contract Tee")

    with TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
            product_image = ProductImage.objects.create(
                product=product,
                image=make_test_image(),
                alt_text="Storage contract main shot",
                is_main=True,
            )

            stored_path = Path(media_root) / product_image.image.name
            assert product_image.image.name.startswith("products/")
            assert stored_path.exists()

            response = api_client.get(f"/api/v1/products/{product.slug}/")

    assert response.status_code == 200
    assert response.data["main_image"]["alt_text"] == "Storage contract main shot"
    assert response.data["main_image"]["url"].endswith(product_image.image.name)
    assert response.data["images"][0]["url"].endswith(product_image.image.name)
