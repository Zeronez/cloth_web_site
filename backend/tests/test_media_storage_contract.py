from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from catalog.models import ProductImage


pytestmark = pytest.mark.django_db


def test_product_images_persist_through_configured_storage_and_product_api(
    api_client, product_factory
):
    product = product_factory(name="Storage Contract Tee")

    with TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
            product_image = ProductImage.objects.create(
                product=product,
                image=SimpleUploadedFile(
                    "storage-tee.jpg",
                    b"fake-jpeg-bytes",
                    content_type="image/jpeg",
                ),
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
