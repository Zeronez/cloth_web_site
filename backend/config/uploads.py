from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def _file_size(uploaded_file):
    size = getattr(uploaded_file, "size", None)
    if size is not None:
        return size
    if not hasattr(uploaded_file, "tell") or not hasattr(uploaded_file, "seek"):
        return 0
    current = uploaded_file.tell()
    uploaded_file.seek(0, 2)
    size = uploaded_file.tell()
    uploaded_file.seek(current)
    return size


def _reset(uploaded_file):
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)


def validate_image_upload(uploaded_file, *, max_bytes, label):
    if not uploaded_file:
        return

    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"{label}: поддерживаются только JPG, PNG или WEBP файлы."
        )

    size = _file_size(uploaded_file)
    if size > max_bytes:
        max_mb = round(max_bytes / (1024 * 1024), 1)
        raise ValidationError(f"{label}: файл превышает допустимый размер {max_mb} МБ.")

    content_type = getattr(uploaded_file, "content_type", "")
    if content_type and not str(content_type).lower().startswith("image/"):
        raise ValidationError(f"{label}: файл должен быть изображением.")

    try:
        _reset(uploaded_file)
        with Image.open(uploaded_file) as image:
            image.verify()

        _reset(uploaded_file)
        with Image.open(uploaded_file) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError(f"{label}: формат изображения не поддерживается.")
            width, height = image.size
            if width <= 0 or height <= 0:
                raise ValidationError(
                    f"{label}: изображение повреждено или имеет некорректные размеры."
                )
            if width * height > settings.IMAGE_UPLOAD_MAX_PIXELS:
                raise ValidationError(
                    f"{label}: изображение слишком большое по разрешению."
                )
    except UnidentifiedImageError as exc:
        raise ValidationError(
            f"{label}: файл не является корректным изображением."
        ) from exc
    finally:
        _reset(uploaded_file)


def validate_avatar_upload(uploaded_file):
    validate_image_upload(
        uploaded_file,
        max_bytes=settings.AVATAR_UPLOAD_MAX_BYTES,
        label="Аватар",
    )


def validate_product_image_upload(uploaded_file):
    validate_image_upload(
        uploaded_file,
        max_bytes=settings.PRODUCT_IMAGE_UPLOAD_MAX_BYTES,
        label="Изображение товара",
    )
