from io import BytesIO
from tempfile import TemporaryDirectory

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from catalog.models import ProductImage


pytestmark = pytest.mark.django_db


def make_test_image(*, name="test.png", image_format="PNG", size=(10, 10)):
    buffer = BytesIO()
    Image.new("RGB", size, color=(120, 20, 220)).save(buffer, format=image_format)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type=f"image/{image_format.lower()}",
    )


def test_product_image_rejects_invalid_extension(product_factory):
    product = product_factory(name="Upload Validation Tee")

    with pytest.raises(ValidationError, match="поддерживаются только"):
        ProductImage.objects.create(
            product=product,
            image=SimpleUploadedFile(
                "payload.txt",
                b"not-an-image",
                content_type="text/plain",
            ),
            alt_text="Invalid upload",
        )


def test_product_image_rejects_oversized_file(product_factory):
    product = product_factory(name="Oversized Upload Tee")
    oversized = SimpleUploadedFile(
        "oversized.png",
        b"x" * 2048,
        content_type="image/png",
    )

    with override_settings(PRODUCT_IMAGE_UPLOAD_MAX_BYTES=1024):
        with pytest.raises(ValidationError, match="превышает допустимый размер"):
            ProductImage.objects.create(
                product=product,
                image=oversized,
                alt_text="Oversized upload",
            )


def test_avatar_rejects_non_image_content(user):
    with pytest.raises(ValidationError, match="корректным изображением"):
        user.avatar = SimpleUploadedFile(
            "avatar.png",
            b"fake-image-bytes",
            content_type="image/png",
        )
        user.save()


def test_avatar_accepts_valid_image(user):
    with TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
            user.avatar = make_test_image(name="avatar.webp", image_format="WEBP")
            user.save()

    user.refresh_from_db()
    assert user.avatar.name.startswith("avatars/")
