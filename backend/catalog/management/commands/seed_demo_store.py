from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import AnimeFranchise, Category, Product, ProductVariant
from delivery.models import DeliveryMethod
from payments.models import PaymentMethod


class Command(BaseCommand):
    help = "Seed AnimeAttire with Russian demo catalog, delivery and payment data."

    def handle(self, *args, **options):
        with transaction.atomic():
            categories = self._seed_categories()
            franchises = self._seed_franchises()
            self._seed_products(categories, franchises)
            self._seed_delivery_methods()
            self._seed_payment_methods()

        self.stdout.write(self.style.SUCCESS("AnimeAttire demo data is ready."))

    def _seed_categories(self):
        data = [
            ("hoodies", "Худи", "Плотные худи для дропов и повседневного streetwear."),
            (
                "t-shirts",
                "Футболки",
                "Футболки с аниме-графикой и лимитированными принтами.",
            ),
            ("jackets", "Куртки", "Верхняя одежда с киберпанк-силуэтом."),
            ("pants", "Брюки", "Карго и нижний слой для streetwear-комплектов."),
            ("accessories", "Аксессуары", "Сумки, шапки и детали для полного образа."),
        ]
        return {
            slug: Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                },
            )[0]
            for slug, name, description in data
        }

    def _seed_franchises(self):
        data = [
            ("original", "AnimeAttire Original", "Оригинальные дизайны AnimeAttire."),
            ("shonen-core", "Сёнен Core", "Энергия турнирных арок и неоновых улиц."),
            ("cyber-saga", "Кибер Сага", "Техно-нуар, мегаполисы и ночной свет."),
            (
                "mecha-dream",
                "Mecha Dream",
                "Меха-эстетика, панели и индустриальные акценты.",
            ),
        ]
        return {
            slug: AnimeFranchise.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                },
            )[0]
            for slug, name, description in data
        }

    def _seed_products(self, categories, franchises):
        products = [
            {
                "slug": "neon-ronin-shell",
                "name": "Куртка Neon Ronin",
                "category": categories["jackets"],
                "franchise": franchises["cyber-saga"],
                "description": (
                    "Легкая городская куртка с контрастными панелями, высоким воротом "
                    "и посадкой под многослойный образ."
                ),
                "base_price": Decimal("14800.00"),
                "is_featured": True,
                "variants": [
                    ("AA-NRS-BLK-M", ProductVariant.Size.M, "Черный", 8),
                    ("AA-NRS-BLK-L", ProductVariant.Size.L, "Черный", 7),
                    ("AA-NRS-SLV-M", ProductVariant.Size.M, "Серебро", 4),
                ],
            },
            {
                "slug": "arcade-alley-hoodie",
                "name": "Худи Arcade Alley",
                "category": categories["hoodies"],
                "franchise": franchises["shonen-core"],
                "description": (
                    "Тяжелое худи с объемным капюшоном, мягким футером и графикой "
                    "в духе игровых залов поздней ночи."
                ),
                "base_price": Decimal("9600.00"),
                "is_featured": True,
                "variants": [
                    ("AA-AAH-GRF-S", ProductVariant.Size.S, "Графит", 10),
                    ("AA-AAH-GRF-M", ProductVariant.Size.M, "Графит", 14),
                    ("AA-AAH-RED-L", ProductVariant.Size.L, "Красный", 6),
                ],
            },
            {
                "slug": "signal-cargo-pants",
                "name": "Карго Signal",
                "category": categories["pants"],
                "franchise": franchises["mecha-dream"],
                "description": (
                    "Функциональные карго с усиленными карманами, регулируемой посадкой "
                    "и лаконичными техно-лейблами."
                ),
                "base_price": Decimal("11800.00"),
                "is_featured": False,
                "variants": [
                    ("AA-SCP-BLK-M", ProductVariant.Size.M, "Черный", 9),
                    ("AA-SCP-BLK-L", ProductVariant.Size.L, "Черный", 9),
                    ("AA-SCP-OLV-M", ProductVariant.Size.M, "Оливковый", 5),
                ],
            },
            {
                "slug": "ghost-frame-tee",
                "name": "Футболка Ghost Frame",
                "category": categories["t-shirts"],
                "franchise": franchises["original"],
                "description": (
                    "Плотная футболка оверсайз с мягким воротом и монохромным принтом "
                    "для базового слоя."
                ),
                "base_price": Decimal("4200.00"),
                "is_featured": False,
                "variants": [
                    ("AA-GFT-WHT-S", ProductVariant.Size.S, "Белый", 16),
                    ("AA-GFT-WHT-M", ProductVariant.Size.M, "Белый", 18),
                    ("AA-GFT-BLK-L", ProductVariant.Size.L, "Черный", 12),
                ],
            },
        ]

        for item in products:
            variants = item.pop("variants")
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **item,
                    "is_active": True,
                },
            )
            for sku, size, color, stock in variants:
                ProductVariant.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "product": product,
                        "size": size,
                        "color": color,
                        "stock_quantity": stock,
                        "price_delta": Decimal("0.00"),
                        "is_active": True,
                    },
                )

    def _seed_delivery_methods(self):
        methods = [
            {
                "code": "pickup-point",
                "name": "Пункт выдачи",
                "kind": DeliveryMethod.Kind.PICKUP,
                "description": "Самовывоз из партнерского пункта выдачи после подтверждения заказа.",
                "price_amount": Decimal("0.00"),
                "estimated_days_min": 2,
                "estimated_days_max": 4,
                "requires_address": True,
                "sort_order": 10,
            },
            {
                "code": "courier-cis",
                "name": "Курьерская доставка",
                "kind": DeliveryMethod.Kind.COURIER,
                "description": "Курьерская доставка по выбранному городу после ручного подтверждения.",
                "price_amount": Decimal("390.00"),
                "estimated_days_min": 1,
                "estimated_days_max": 3,
                "requires_address": True,
                "sort_order": 20,
            },
        ]
        for method in methods:
            DeliveryMethod.objects.update_or_create(
                code=method["code"],
                defaults={**method, "currency": "RUB", "is_active": True},
            )

    def _seed_payment_methods(self):
        PaymentMethod.objects.update_or_create(
            code="manual-card",
            defaults={
                "name": "Банковская карта",
                "description": (
                    "Локальная платежная сессия для стенда. Реальный платежный "
                    "провайдер подключается отдельно."
                ),
                "provider_code": "placeholder",
                "session_mode": PaymentMethod.SessionMode.PLACEHOLDER,
                "currency": "RUB",
                "is_active": True,
                "sort_order": 10,
            },
        )
