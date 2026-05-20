import base64
import random
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


# 1x1 PNG
PLACEHOLDER_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="


def placeholder_image(*, name: str) -> SimpleUploadedFile:
    content = base64.b64decode(PLACEHOLDER_PNG_BASE64)
    return SimpleUploadedFile(name=name, content=content, content_type="image/png")


def seed_categories() -> list[Category]:
    categories = [
        ("hoodies", "Худи", "Теплые худи и свитшоты."),
        ("tshirts", "Футболки", "Футболки на каждый день."),
        ("outerwear", "Верхняя одежда", "Куртки, бомберы и другое."),
        ("accessories", "Аксессуары", "Сумки, носки, шапки и другое."),
    ]
    result: list[Category] = []
    for slug, name, description in categories:
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "is_active": True,
            },
        )
        result.append(category)
    return result


def seed_franchises() -> list[AnimeFranchise]:
    franchises = [
        ("naruto", "Наруто"),
        ("aot", "Атака титанов"),
        ("jjk", "Магическая битва"),
        ("eva", "Евангелион"),
    ]
    result: list[AnimeFranchise] = []
    for slug, name in franchises:
        franchise, _ = AnimeFranchise.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": "", "is_active": True},
        )
        result.append(franchise)
    return result


def make_product_name(franchise_name: str, index: int) -> str:
    adjectives = [
        "Оверсайз",
        "Лимитированный",
        "Плотный",
        "Стрит",
        "Премиум",
        "Ночной",
        "Глитч",
        "Неон",
    ]
    items = ["худи", "футболка", "бомбер", "лонгслив"]
    return (
        f"{random.choice(adjectives)} {random.choice(items)} {franchise_name} #{index}"
    )


def make_description(franchise_name: str) -> str:
    return (
        f"Дроп вдохновлён «{franchise_name}». Плотный материал, аккуратные швы, "
        "комфортный крой. Фото — заглушка, реальный контент будет добавлен перед продом."
    )


def variant_specs() -> list[dict]:
    return [
        {"size": ProductVariant.Size.S, "color": "Black"},
        {"size": ProductVariant.Size.M, "color": "Black"},
        {"size": ProductVariant.Size.L, "color": "Black"},
        {"size": ProductVariant.Size.M, "color": "White"},
    ]


@transaction.atomic
def seed_products(*, count: int) -> int:
    categories = seed_categories()
    franchises = seed_franchises()

    created = 0
    for i in range(1, count + 1):
        franchise = random.choice(franchises)
        category = random.choice(categories)
        name = make_product_name(franchise.name, i)
        base_price = Decimal(
            random.choice(["2990.00", "3490.00", "3990.00", "4590.00"])
        )

        product, was_created = Product.objects.get_or_create(
            slug=f"demo-{franchise.slug}-{i}",
            defaults={
                "name": name,
                "description": make_description(franchise.name),
                "base_price": base_price,
                "currency": "RUB",
                "status": Product.PublishingStatus.ACTIVE,
                "is_active": True,
                "is_featured": i <= 3,
                "category": category,
                "franchise": franchise,
                "material": "Хлопок/полиэстер",
                "fit": "Оверсайз",
                "care": "Деликатная стирка 30°C, без отбеливателя.",
            },
        )

        if not was_created:
            continue

        created += 1

        for spec in variant_specs():
            sku = f"DEMO-{franchise.slug.upper()}-{i:03d}-{spec['color'][0]}-{spec['size']}"
            ProductVariant.objects.create(
                product=product,
                sku=sku,
                size=spec["size"],
                color=spec["color"],
                stock_quantity=random.randint(0, 25),
                price_delta=Decimal("0.00"),
                is_active=True,
            )

        ProductImage.objects.create(
            product=product,
            image=placeholder_image(name=f"demo-{product.slug}.png"),
            alt_text=f"Фото товара {product.name} (заглушка)",
            is_main=True,
            sort_order=0,
            is_approved=True,
        )

    return created


class Command(BaseCommand):
    help = "Seed the database with demo catalog products (placeholder images)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=24)

    def handle(self, *args, **options):
        count = int(options["count"])
        created = seed_products(count=count)
        self.stdout.write(
            self.style.SUCCESS(f"Seed complete. Created {created} products.")
        )
