from pathlib import Path
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import AnimeFranchise, Category, Product, ProductImage, ProductVariant
from delivery.models import DeliveryMethod
from payments.models import PaymentMethod


class Command(BaseCommand):
    help = "Seed AnimeAttire with Russian demo catalog, delivery and payment data."

    def handle(self, *args, **options):
        with transaction.atomic():
            # Keep local dev storefront clean: remove legacy placeholder demo catalog
            # entries (seed_demo_catalog) so the frontend doesn't show 1x1 "empty" images.
            Product.objects.filter(slug__startswith="demo-").delete()
            categories = self._seed_categories()
            franchises = self._seed_franchises()
            self._seed_products(categories, franchises)
            self._seed_delivery_methods()
            self._seed_payment_methods()

        self.stdout.write(self.style.SUCCESS("AnimeAttire demo data is ready."))

    def _stock_file(self, filename: str) -> Path:
        # __file__ = backend/catalog/management/commands/seed_demo_store.py
        # parents[4] = repo root (cloth_web_site)
        return Path(__file__).resolve().parents[4] / "stock files" / filename

    def _upsert_named_record(self, model, *, slug: str, name: str, defaults: dict):
        instance = model.objects.filter(slug=slug).first()
        if instance is None:
            instance = model.objects.filter(name=name).first()

        if instance is None:
            return model.objects.create(slug=slug, name=name, **defaults)

        for field, value in {"slug": slug, "name": name, **defaults}.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def _load_stock_image(self, filename: str) -> SimpleUploadedFile | None:
        path = self._stock_file(filename)
        if not path.exists():
            self.stdout.write(
                self.style.WARNING(f"Stock image not found, skipping: {path}")
            )
            return None
        return SimpleUploadedFile(
            name=path.name,
            content=path.read_bytes(),
            content_type="image/webp",
        )

    def _seed_categories(self):
        data = [
            ("hoodies", "Худи", "Плотные худи для дропов и повседневного streetwear."),
            (
                "tshirts",
                "Футболки",
                "Футболки с аниме-графикой и лимитированными принтами.",
            ),
            (
                "bodysuits",
                "Боди",
                "Боди с мягким трикотажем, плотной посадкой и аниме-принтами.",
            ),
            (
                "longsleeves",
                "Лонгсливы",
                "Лонгсливы для многослойных образов и прохладной погоды.",
            ),
            (
                "jerseys",
                "Джерси",
                "Оверсайз джерси из сетки и спортивного трикотажа.",
            ),
            (
                "sweatshirts",
                "Свитшоты",
                "Свитшоты и quarter-zip модели для холодного сезона.",
            ),
            ("jackets", "Куртки", "Верхняя одежда с киберпанк-силуэтом."),
            ("pants", "Брюки", "Карго и нижний слой для streetwear-комплектов."),
            ("accessories", "Аксессуары", "Сумки, шапки и детали для полного образа."),
        ]
        return {
            slug: self._upsert_named_record(
                Category,
                slug=slug,
                name=name,
                defaults={
                    "description": description,
                    "is_active": True,
                },
            )
            for slug, name, description in data
        }

    def _seed_franchises(self):
        data = [
            ("original", "AnimeAttire Original", "Оригинальные дизайны AnimeAttire."),
            ("shonen-core", "Сёнен Core", "Энергия турнирных арок и неоновых улиц."),
            ("cyber-saga", "Кибер Сага", "Техно-нуар, мегаполисы и ночной свет."),
            ("berserk", "Берсерк", "Тёмное фэнтези, металл и stone-wash эстетика."),
            ("naruto", "Наруто", "Ниндзя-сюжет, символика и streetwear вайб."),
            ("eva", "Евангелион", "Меха-икона и техно-эстетика."),
            (
                "chainsaw-man",
                "Человек-бензопила",
                "Агрессивный уличный вайб, хоррор-экшен и острые графические формы.",
            ),
            (
                "jujutsu-kaisen",
                "Магическая битва",
                "Проклятая энергия, контрастные знаки и современный shonen-ритм.",
            ),
            (
                "my-hero-academia",
                "Моя геройская академия",
                "Геройские мотивы, динамичные принты и спортивный силуэт.",
            ),
            ("akira", "Акира", "Нео-Токио, скорость и техно-антиутопия."),
            ("dandadan", "Дандадан", "Драйв, хоррор-экшен и дерзкий стрит."),
            (
                "mecha-dream",
                "Mecha Dream",
                "Меха-эстетика, панели и индустриальные акценты.",
            ),
        ]
        return {
            slug: self._upsert_named_record(
                AnimeFranchise,
                slug=slug,
                name=name,
                defaults={
                    "description": description,
                    "is_active": True,
                },
            )
            for slug, name, description in data
        }

    def _seed_products(self, categories, franchises):
        products = [
            {
                "slug": "gojo-satoru-zip-hoodie",
                "name": 'Зип худи "Gojo Satoru"',
                "category": categories["hoodies"],
                "franchise": franchises["shonen-core"],
                "description": (
                    "Плотный футер 3-х нитка с начесом и надежные нашивки на левом рукаве. "
                    "Состав: 80% хлопок, 20% полиэстер (высшая категория качества). "
                    "Срок производства: 5–7 рабочих дней (без учета выходных)."
                ),
                "base_price": Decimal("8490.00"),
                "is_featured": False,
                "variants": [
                    ("AA-GSJ-ZIP-BLK-S", ProductVariant.Size.S, "Чёрный", 12),
                    ("AA-GSJ-ZIP-BLK-M", ProductVariant.Size.M, "Чёрный", 12),
                    ("AA-GSJ-ZIP-BLK-L", ProductVariant.Size.L, "Чёрный", 9),
                ],
                "images": [
                    {
                        "filename": "1-1 зип худи Gojo Satoru.webp",
                        "alt_text": 'Зип худи "Gojo Satoru" — фото 1',
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "1-2 зип худи Gojo Satoru .webp",
                        "alt_text": 'Зип худи "Gojo Satoru" — фото 2',
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "berserk-stone-wash-pants",
                "name": "Штаны | BERSERK (STONE WASH)",
                "category": categories["pants"],
                "franchise": franchises["berserk"],
                "description": (
                    "Широкие брюки с фирменной металлической фурнитурой в виде лого на штанине. "
                    "Эластичный пояс со шнурком для удобной посадки. "
                    "Уход: стирка до 40°C (деликатный/ручной режим), без пятновыводителей. "
                    "Срок производства: от 30 дней."
                ),
                "base_price": Decimal("14590.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BSWP-STW-S", ProductVariant.Size.S, "Stone Wash", 6),
                    ("AA-BSWP-STW-M", ProductVariant.Size.M, "Stone Wash", 6),
                    ("AA-BSWP-STW-L", ProductVariant.Size.L, "Stone Wash", 4),
                ],
                "images": [
                    {
                        "filename": "2-1 ШТАНЫ  BERSERK (STONE WASH).webp",
                        "alt_text": "Штаны BERSERK (STONE WASH) — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "2-2 ШТАНЫ  BERSERK (STONE WASH).webp",
                        "alt_text": "Штаны BERSERK (STONE WASH) — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "femto-hoodie-r",
                "name": "Худи | FEMTO (R)",
                "category": categories["hoodies"],
                "franchise": franchises["berserk"],
                "description": (
                    "Тёплый худи из высококачественного хлопка с мягким начёсом. "
                    "Состав: 70% хлопок, 30% полиэстер. Цвет: чёрный."
                ),
                "base_price": Decimal("12490.00"),
                "is_featured": False,
                "variants": [
                    ("AA-FHR-BLK-S", ProductVariant.Size.S, "Чёрный", 8),
                    ("AA-FHR-BLK-M", ProductVariant.Size.M, "Чёрный", 10),
                    ("AA-FHR-BLK-L", ProductVariant.Size.L, "Чёрный", 7),
                ],
                "images": [
                    {
                        "filename": "3-1 ХУДИ FEMTO (R).webp",
                        "alt_text": "Худи FEMTO (R) — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "3-2 ХУДИ FEMTO (R).webp",
                        "alt_text": "Худи FEMTO (R) — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "3-3 ХУДИ FEMTO (R).webp",
                        "alt_text": "Худи FEMTO (R) — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "3-4 ХУДИ FEMTO (R).webp",
                        "alt_text": "Худи FEMTO (R) — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                    {
                        "filename": "3-5 ХУДИ FEMTO (R).webp",
                        "alt_text": "Худи FEMTO (R) — фото 5",
                        "is_main": False,
                        "sort_order": 40,
                    },
                ],
            },
            {
                "slug": "fate-zip-hoodie",
                "name": "Худи на молнии | FATE",
                "category": categories["hoodies"],
                "franchise": franchises["berserk"],
                "description": (
                    "Худи на молнии из ткани интерсофт средней плотности. "
                    "Мягкий зип-худи для прохладной погоды, карман-кенгуру со скрытыми кармашками. "
                    "Материал: 65% полиэстер / 35% хлопок. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("14190.00"),
                "is_featured": False,
                "variants": [
                    ("AA-FZH-BLK-S", ProductVariant.Size.S, "Чёрный", 6),
                    ("AA-FZH-BLK-M", ProductVariant.Size.M, "Чёрный", 8),
                    ("AA-FZH-BLK-L", ProductVariant.Size.L, "Чёрный", 6),
                ],
                "images": [
                    {
                        "filename": "ХУДИ НА МОЛНИИ FATE 4-1.webp",
                        "alt_text": "Худи на молнии FATE — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "ХУДИ НА МОЛНИИ FATE 4-2.webp",
                        "alt_text": "Худи на молнии FATE — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "ХУДИ НА МОЛНИИ FATE 4-3.webp",
                        "alt_text": "Худи на молнии FATE — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "ХУДИ НА МОЛНИИ FATE 4-4.webp",
                        "alt_text": "Худи на молнии FATE — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                ],
            },
            {
                "slug": "turbogranny-denim-bomber",
                "name": "Джинсовый бомбер | TURBOGRANNY",
                "category": categories["jackets"],
                "franchise": franchises["dandadan"],
                "description": (
                    "Бомбер из плотной джинсовой ткани: классический силуэт, отложной воротник, "
                    "трикотажные подвязы, прорезные карманы, фирменные кнопки. "
                    "Принт: ДТФ печать + золотая термоплёнка. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("22990.00"),
                "is_featured": False,
                "variants": [
                    ("AA-TDB-BLU-S", ProductVariant.Size.S, "Синий деним", 3),
                    ("AA-TDB-BLU-M", ProductVariant.Size.M, "Синий деним", 4),
                    ("AA-TDB-BLU-L", ProductVariant.Size.L, "Синий деним", 3),
                ],
                "images": [
                    {
                        "filename": "bomber-turbogranny-vis-bc-5-1.webp",
                        "alt_text": "Джинсовый бомбер TURBOGRANNY — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "bomber-turbogranny-vis-bc-5-2.webp",
                        "alt_text": "Джинсовый бомбер TURBOGRANNY — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "dragons-bag",
                "name": "Сумка | DRAGONS",
                "category": categories["accessories"],
                "franchise": None,
                "description": (
                    "Мягкая, легкая и удобная сумка из 100% хлопка с фирменным поясом. "
                    "Размеры: 17.5×22×3 см. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("5290.00"),
                "is_featured": False,
                "variants": [
                    (
                        "AA-DBG-BLK-ONE",
                        ProductVariant.Size.ONE_SIZE,
                        "Чёрный",
                        12,
                    ),
                ],
                "images": [
                    {
                        "filename": "6-1 сумка dragons.webp",
                        "alt_text": "Сумка DRAGONS — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "6-2 сумка dragons.webp",
                        "alt_text": "Сумка DRAGONS — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "6-3 сумка dragons.webp",
                        "alt_text": "Сумка DRAGONS — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "6-4 сумка dragons.webp",
                        "alt_text": "Сумка DRAGONS — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                    {
                        "filename": "6-5 сумка dragons.webp",
                        "alt_text": "Сумка DRAGONS — фото 5",
                        "is_main": False,
                        "sort_order": 40,
                    },
                ],
            },
            {
                "slug": "beige-cargo-pants",
                "name": "Штаны карго | BEIGE",
                "category": categories["pants"],
                "franchise": None,
                "description": (
                    "Карго-брюки оверсайз силуэта из варёного хлопка. Эластичный пояс, резинки по низу штанин, "
                    "два больших боковых кармана. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("9400.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BCP-BEI-S", ProductVariant.Size.S, "Бежевый", 7),
                    ("AA-BCP-BEI-M", ProductVariant.Size.M, "Бежевый", 8),
                    ("AA-BCP-BEI-L", ProductVariant.Size.L, "Бежевый", 6),
                ],
                "images": [
                    {
                        "filename": "7-1 ШТАНЫ КАРГО BEIGE.webp",
                        "alt_text": "Штаны карго BEIGE — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "7-2 ШТАНЫ КАРГО BEIGE.webp",
                        "alt_text": "Штаны карго BEIGE — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "cursed-snake-zip-sweatshirt",
                "name": "Свитшот на молнии | CURSED SNAKE",
                "category": categories["hoodies"],
                "franchise": franchises["naruto"],
                "description": (
                    "Объемный свитшот на молнии с длинным рукавом. Футер 3х нитка петля, свободный крой. "
                    "Цвет: чёрный. Материал: 80% хлопок / 20% полиэстер. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("10000.00"),
                "is_featured": False,
                "variants": [
                    ("AA-CSZ-BLK-S", ProductVariant.Size.S, "Чёрный", 6),
                    ("AA-CSZ-BLK-M", ProductVariant.Size.M, "Чёрный", 8),
                    ("AA-CSZ-BLK-L", ProductVariant.Size.L, "Чёрный", 6),
                ],
                "images": [
                    {
                        "filename": "8-1 CURSED SNAKE.webp",
                        "alt_text": "Свитшот CURSED SNAKE — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "8-2 CURSED SNAKE.webp",
                        "alt_text": "Свитшот CURSED SNAKE — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "eva02-asuka-tee",
                "name": "Футболка | EVA02 ASUKA",
                "category": categories["tshirts"],
                "franchise": franchises["eva"],
                "description": (
                    "Лёгкая унисекс футболка из тонкого хлопка с добавлением лайкры для удобной посадки. "
                    "Принт EVA 02 Asuka (Евангелион). Срок производства: от 30 дней."
                ),
                "base_price": Decimal("4150.00"),
                "is_featured": False,
                "variants": [
                    ("AA-EAT-BLK-S", ProductVariant.Size.S, "Чёрный", 10),
                    ("AA-EAT-BLK-M", ProductVariant.Size.M, "Чёрный", 12),
                    ("AA-EAT-BLK-L", ProductVariant.Size.L, "Чёрный", 10),
                ],
                "images": [
                    {
                        "filename": "9-1 ФУТБОЛКА EVA02 ASUKA.webp",
                        "alt_text": "Футболка EVA02 ASUKA — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "9-2 ФУТБОЛКА EVA02 ASUKA.webp",
                        "alt_text": "Футболка EVA02 ASUKA — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "flash-of-the-leaf-tee",
                "name": "Футболка | FLASH OF THE LEAF",
                "category": categories["tshirts"],
                "franchise": franchises["naruto"],
                "description": (
                    "Легкая унисекс футболка из тонкого материала с добавлением лайкры для удобной посадки "
                    "в повседневных занятиях, спорте и активностях. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("4790.00"),
                "is_featured": False,
                "variants": [
                    ("AA-FLT-BLK-S", ProductVariant.Size.S, "Чёрный", 10),
                    ("AA-FLT-BLK-M", ProductVariant.Size.M, "Чёрный", 12),
                    ("AA-FLT-BLK-L", ProductVariant.Size.L, "Чёрный", 10),
                ],
                "images": [
                    {
                        "filename": "10-1 tshirt-flash-of-the-leaf-vis-front.webp",
                        "alt_text": "Футболка FLASH OF THE LEAF — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "10-2 tshirt-flash-of-the-leaf-vis-front.webp",
                        "alt_text": "Футболка FLASH OF THE LEAF — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "power-shot-grey-tee",
                "name": "Футболка | POWER SHOT GREY",
                "category": categories["tshirts"],
                "franchise": franchises["naruto"],
                "description": (
                    "Легкая унисекс футболка с эффектом старения/потёртости. "
                    "Уход: стирка до 30°C (деликатный/ручной режим), стирать вывернув наизнанку, без пятновыводителей. "
                    "Срок производства: от 30 дней."
                ),
                "base_price": Decimal("5490.00"),
                "is_featured": False,
                "variants": [
                    ("AA-PSG-GRY-S", ProductVariant.Size.S, "Серый", 10),
                    ("AA-PSG-GRY-M", ProductVariant.Size.M, "Серый", 12),
                    ("AA-PSG-GRY-L", ProductVariant.Size.L, "Серый", 10),
                ],
                "images": [
                    {
                        "filename": "11-1 sakuravisfront-scaled.webp",
                        "alt_text": "Футболка POWER SHOT GREY — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "11-2 sakuravisfront-scaled.webp",
                        "alt_text": "Футболка POWER SHOT GREY — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "kargo-pants",
                "name": "Штаны | KARGO",
                "category": categories["pants"],
                "franchise": None,
                "description": (
                    "Женские штаны карго из варенного хлопка (100% натуральная ткань), мягкие благодаря специальной обработке. "
                    "8 карманов, смежные размеры для вариативной посадки. Срок производства: от 30 дней."
                ),
                "base_price": Decimal("13690.00"),
                "is_featured": False,
                "variants": [
                    ("AA-KGP-BLK-S", ProductVariant.Size.S, "Чёрный", 6),
                    ("AA-KGP-BLK-M", ProductVariant.Size.M, "Чёрный", 6),
                    ("AA-KGP-BLK-L", ProductVariant.Size.L, "Чёрный", 4),
                ],
                "images": [
                    {
                        "filename": "12-1 ШТАНЫ KARGO.webp",
                        "alt_text": "Штаны KARGO — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "12-2 ШТАНЫ KARGO.webp",
                        "alt_text": "Штаны KARGO — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "12-3 ШТАНЫ KARGO.webp",
                        "alt_text": "Штаны KARGO — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "12-4 ШТАНЫ KARGO.webp",
                        "alt_text": "Штаны KARGO — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                ],
            },
            {
                "slug": "blazonry-body-white",
                "name": "Боди | BLAZONRY WHT",
                "category": categories["bodysuits"],
                "franchise": franchises["berserk"],
                "description": (
                    "Боди из мягкого тянущегося трикотажа с длинными рукавами и потайными кнопками снизу. "
                    "Белая версия принта по мотивам Берсерка для акцентного слоя в образе."
                ),
                "base_price": Decimal("5290.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BBW-WHT-S", ProductVariant.Size.S, "Белый", 5),
                    ("AA-BBW-WHT-M", ProductVariant.Size.M, "Белый", 7),
                    ("AA-BBW-WHT-L", ProductVariant.Size.L, "Белый", 5),
                ],
                "images": [
                    {
                        "filename": "1-1 BODI-blazonry-white.webp",
                        "alt_text": "Боди BLAZONRY WHT — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "1-2 BODI-blazonry-white.webp",
                        "alt_text": "Боди BLAZONRY WHT — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "chainsaw-body",
                "name": "Боди | CHAINSAW",
                "category": categories["bodysuits"],
                "franchise": franchises["chainsaw-man"],
                "description": (
                    "Боди из мягкого трикотажа с длинными рукавами и потайными кнопками снизу. "
                    "Принт по мотивам аниме «Человек-бензопила»."
                ),
                "base_price": Decimal("5790.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BCD-BLK-S", ProductVariant.Size.S, "Чёрный", 5),
                    ("AA-BCD-BLK-M", ProductVariant.Size.M, "Чёрный", 7),
                    ("AA-BCD-BLK-L", ProductVariant.Size.L, "Чёрный", 5),
                ],
                "images": [
                    {
                        "filename": "2-1 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "2-2 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "2-3 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "2-4 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                    {
                        "filename": "2-5 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 5",
                        "is_main": False,
                        "sort_order": 40,
                    },
                    {
                        "filename": "2-6 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 6",
                        "is_main": False,
                        "sort_order": 50,
                    },
                    {
                        "filename": "2-7 BODI-chainsaw.webp",
                        "alt_text": "Боди CHAINSAW — фото 7",
                        "is_main": False,
                        "sort_order": 60,
                    },
                ],
            },
            {
                "slug": "hyuga-tales-body",
                "name": "Боди | HYUGA TALES",
                "category": categories["bodysuits"],
                "franchise": franchises["naruto"],
                "description": (
                    "Боди из мягкого трикотажа с длинными рукавами и потайными кнопками снизу. "
                    "Принт Hyuga Tales по мотивам Наруто. Требует деликатного ухода и стирки до 30°C."
                ),
                "base_price": Decimal("5290.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BHT-BLK-S", ProductVariant.Size.S, "Чёрный", 5),
                    ("AA-BHT-BLK-M", ProductVariant.Size.M, "Чёрный", 7),
                    ("AA-BHT-BLK-L", ProductVariant.Size.L, "Чёрный", 5),
                ],
                "images": [
                    {
                        "filename": "3-1 BODI-HYOGA-TALES.webp",
                        "alt_text": "Боди HYUGA TALES — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "3-2 BODI-HYOGA-TALES.webp",
                        "alt_text": "Боди HYUGA TALES — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "3-3 BODI-HYOGA-TALES.webp",
                        "alt_text": "Боди HYUGA TALES — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "3-4 BODI-HYOGA-TALES.webp",
                        "alt_text": "Боди HYUGA TALES — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                ],
            },
            {
                "slug": "eva01-body",
                "name": "Боди | EVA01",
                "category": categories["bodysuits"],
                "franchise": franchises["eva"],
                "description": (
                    "Боди из мягкого трикотажного полотна с длинными рукавами и потайными кнопками снизу. "
                    "Принт EVA 01 по мотивам аниме «Евангелион»."
                ),
                "base_price": Decimal("5790.00"),
                "is_featured": False,
                "variants": [
                    ("AA-BEV-BLK-S", ProductVariant.Size.S, "Чёрный", 5),
                    ("AA-BEV-BLK-M", ProductVariant.Size.M, "Чёрный", 7),
                    ("AA-BEV-BLK-L", ProductVariant.Size.L, "Чёрный", 5),
                ],
                "images": [
                    {
                        "filename": "4-1 BODI-EVA01.webp",
                        "alt_text": "Боди EVA01 — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "4-2 BODI-EVA01.webp",
                        "alt_text": "Боди EVA01 — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "masks-tee",
                "name": "Футболка | MASKS",
                "category": categories["tshirts"],
                "franchise": None,
                "description": (
                    "Лёгкая унисекс футболка из тонкого хлопка с добавлением лайкры для активного повседневного использования."
                ),
                "base_price": Decimal("4150.00"),
                "is_featured": False,
                "variants": [
                    ("AA-MSK-BLK-S", ProductVariant.Size.S, "Чёрный", 8),
                    ("AA-MSK-BLK-M", ProductVariant.Size.M, "Чёрный", 10),
                    ("AA-MSK-BLK-L", ProductVariant.Size.L, "Чёрный", 8),
                ],
                "images": [
                    {
                        "filename": "5-1 FUTBOLKA-MASKS-scaled.webp",
                        "alt_text": "Футболка MASKS — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "5-2 FUTBOLKA-MASKS-scaled.webp",
                        "alt_text": "Футболка MASKS — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "5-3 FUTBOLKA-MASKS-scaled.webp",
                        "alt_text": "Футболка MASKS — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "5-4 FUTBOLKA-MASKS-scaled.webp",
                        "alt_text": "Футболка MASKS — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                ],
            },
            {
                "slug": "madman-tee",
                "name": "Футболка | MADMAN",
                "category": categories["tshirts"],
                "franchise": franchises["my-hero-academia"],
                "description": (
                    "Лёгкая унисекс футболка из хлопкового трикотажа с лайкрой для удобной посадки и повседневной носки."
                ),
                "base_price": Decimal("5790.00"),
                "is_featured": False,
                "variants": [
                    ("AA-MDM-BLK-S", ProductVariant.Size.S, "Чёрный", 8),
                    ("AA-MDM-BLK-M", ProductVariant.Size.M, "Чёрный", 10),
                    ("AA-MDM-BLK-L", ProductVariant.Size.L, "Чёрный", 8),
                ],
                "images": [
                    {
                        "filename": "6-1 t-shirt-MADMAN.webp",
                        "alt_text": "Футболка MADMAN — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "6-2 t-shirt-MADMAN.webp",
                        "alt_text": "Футболка MADMAN — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "chainsaw-man-longsleeve",
                "name": "Лонгслив | CHAINSAW MAN",
                "category": categories["longsleeves"],
                "franchise": franchises["chainsaw-man"],
                "description": (
                    "Унисекс лонгслив с эластичной горловиной из дышащего хлопка. "
                    "Подходит для многослойных комплектов и прохладной погоды."
                ),
                "base_price": Decimal("5590.00"),
                "is_featured": False,
                "variants": [
                    ("AA-LCM-BLK-S", ProductVariant.Size.S, "Чёрный", 7),
                    ("AA-LCM-BLK-M", ProductVariant.Size.M, "Чёрный", 9),
                    ("AA-LCM-BLK-L", ProductVariant.Size.L, "Чёрный", 7),
                ],
                "images": [
                    {
                        "filename": "7-1 LONGSLIV-CHAINSAW-MAN-pred-scaled.webp",
                        "alt_text": "Лонгслив CHAINSAW MAN — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "7-2 LONGSLIV-CHAINSAW-MAN-pred-scaled.webp",
                        "alt_text": "Лонгслив CHAINSAW MAN — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "7-3 LONGSLIV-CHAINSAW-MAN-pred-scaled.webp",
                        "alt_text": "Лонгслив CHAINSAW MAN — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                    {
                        "filename": "7-4 LONGSLIV-CHAINSAW-MAN-pred-scaled.webp",
                        "alt_text": "Лонгслив CHAINSAW MAN — фото 4",
                        "is_main": False,
                        "sort_order": 30,
                    },
                    {
                        "filename": "7-5 LONGSLIV-CHAINSAW-MAN-pred-scaled.webp",
                        "alt_text": "Лонгслив CHAINSAW MAN — фото 5",
                        "is_main": False,
                        "sort_order": 40,
                    },
                ],
            },
            {
                "slug": "kanseitai-longsleeve",
                "name": "Лонгслив | KANSEITAI",
                "category": categories["longsleeves"],
                "franchise": franchises["naruto"],
                "description": (
                    "Унисекс лонгслив с эластичной горловиной из качественного хлопка для активной повседневной носки."
                ),
                "base_price": Decimal("5790.00"),
                "is_featured": False,
                "variants": [
                    ("AA-LKN-BLK-S", ProductVariant.Size.S, "Чёрный", 7),
                    ("AA-LKN-BLK-M", ProductVariant.Size.M, "Чёрный", 9),
                    ("AA-LKN-BLK-L", ProductVariant.Size.L, "Чёрный", 7),
                ],
                "images": [
                    {
                        "filename": "8-1 KANSEITAI.webp",
                        "alt_text": "Лонгслив KANSEITAI — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "8-2 KANSEITAI.webp",
                        "alt_text": "Лонгслив KANSEITAI — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "anbu-ninja-longsleeve",
                "name": "Лонгслив | ANBU NINJA",
                "category": categories["longsleeves"],
                "franchise": franchises["naruto"],
                "description": (
                    "Унисекс лонгслив с эластичной горловиной и свободной посадкой. "
                    "Срок производства: от 30 дней."
                ),
                "base_price": Decimal("5690.00"),
                "is_featured": False,
                "variants": [
                    ("AA-LAN-BLK-S", ProductVariant.Size.S, "Чёрный", 6),
                    ("AA-LAN-BLK-M", ProductVariant.Size.M, "Чёрный", 8),
                    ("AA-LAN-BLK-L", ProductVariant.Size.L, "Чёрный", 6),
                ],
                "images": [
                    {
                        "filename": "9-1 ANBU-NINJA-pered-scaled.webp",
                        "alt_text": "Лонгслив ANBU NINJA — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "9-2 ANBU-NINJA-pered-scaled.webp",
                        "alt_text": "Лонгслив ANBU NINJA — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "ghost-of-uchiha-jersey",
                "name": "Джерси | GHOST OF UCHIHA",
                "category": categories["jerseys"],
                "franchise": franchises["naruto"],
                "description": (
                    "Оверсайз джерси из мягкой высококачественной сетки с треугольной горловиной и разрезами по бокам. "
                    "Принт выполнен по технологии сублимации."
                ),
                "base_price": Decimal("10590.00"),
                "is_featured": False,
                "variants": [
                    ("AA-JGU-BLK-S", ProductVariant.Size.S, "Чёрный", 4),
                    ("AA-JGU-BLK-M", ProductVariant.Size.M, "Чёрный", 5),
                    ("AA-JGU-BLK-L", ProductVariant.Size.L, "Чёрный", 4),
                ],
                "images": [
                    {
                        "filename": "10-1 GHOST OF UCHIHA.webp",
                        "alt_text": "Джерси GHOST OF UCHIHA — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "10-2 GHOST OF UCHIHA.webp",
                        "alt_text": "Джерси GHOST OF UCHIHA — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "jiraiya-gallant-quarter-zip",
                "name": "Свитшот на молнии | JIRAIYA: THE GALLANT",
                "category": categories["sweatshirts"],
                "franchise": franchises["naruto"],
                "description": (
                    "Объёмный свитшот с длинным рукавом из футера 3х нитка петля. "
                    "Свободный крой и материал 80% хлопок / 20% полиэстер, срок производства: от 30 дней."
                ),
                "base_price": Decimal("10000.00"),
                "is_featured": False,
                "variants": [
                    ("AA-QJG-BLK-S", ProductVariant.Size.S, "Чёрный", 4),
                    ("AA-QJG-BLK-M", ProductVariant.Size.M, "Чёрный", 5),
                    ("AA-QJG-BLK-L", ProductVariant.Size.L, "Чёрный", 4),
                    ("AA-QJG-BLK-XL", ProductVariant.Size.XL, "Чёрный", 3),
                ],
                "images": [
                    {
                        "filename": "11-1 QUARTER-ZIP-JIRAIYA-THE-GALLANT-vizualizatsiya.webp",
                        "alt_text": "Свитшот JIRAIYA: THE GALLANT — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "11-2 QUARTER-ZIP-JIRAIYA-THE-GALLANT-vizualizatsiya.webp",
                        "alt_text": "Свитшот JIRAIYA: THE GALLANT — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "11-3 QUARTER-ZIP-JIRAIYA-THE-GALLANT-vizualizatsiya.webp",
                        "alt_text": "Свитшот JIRAIYA: THE GALLANT — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                ],
            },
            {
                "slug": "neo-tokyo-experiment-quarter-zip",
                "name": "Свитшот на молнии | NEO TOKYO EXPERIMENT",
                "category": categories["sweatshirts"],
                "franchise": franchises["akira"],
                "description": (
                    "Объёмный свитшот с длинным рукавом из дышащего футера 3х нитка петля. "
                    "Срок производства: от 30 дней."
                ),
                "base_price": Decimal("10000.00"),
                "is_featured": False,
                "variants": [
                    ("AA-QNT-BLK-S", ProductVariant.Size.S, "Чёрный", 4),
                    ("AA-QNT-BLK-M", ProductVariant.Size.M, "Чёрный", 5),
                    ("AA-QNT-BLK-L", ProductVariant.Size.L, "Чёрный", 4),
                ],
                "images": [
                    {
                        "filename": "12-1 quarter-akira-krasn-vis-aktualno-spina.webp",
                        "alt_text": "Свитшот NEO TOKYO EXPERIMENT — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "12-2 quarter-akira-krasn-vis-aktualno-spina.webp",
                        "alt_text": "Свитшот NEO TOKYO EXPERIMENT — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
            {
                "slug": "ryomen-sukuna-quarter-zip",
                "name": "Свитшот на молнии | RYOMEN SUKUNA",
                "category": categories["sweatshirts"],
                "franchise": franchises["jujutsu-kaisen"],
                "description": (
                    "Объёмный свитшот с длинным рукавом из футера 3х нитка петля. "
                    "Срок производства: от 30 дней, материал 80% хлопок / 20% полиэстер."
                ),
                "base_price": Decimal("10000.00"),
                "is_featured": False,
                "variants": [
                    ("AA-QRS-BLK-S", ProductVariant.Size.S, "Чёрный", 4),
                    ("AA-QRS-BLK-M", ProductVariant.Size.M, "Чёрный", 5),
                    ("AA-QRS-BLK-L", ProductVariant.Size.L, "Чёрный", 4),
                    ("AA-QRS-BLK-XL", ProductVariant.Size.XL, "Чёрный", 3),
                ],
                "images": [
                    {
                        "filename": "13-1 kvaterzip-sukuna-vizualizatsiya.webp",
                        "alt_text": "Свитшот RYOMEN SUKUNA — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "13-2 kvaterzip-sukuna-vizualizatsiya.webp",
                        "alt_text": "Свитшот RYOMEN SUKUNA — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                    {
                        "filename": "13-3 kvaterzip-sukuna-vizualizatsiya.webp",
                        "alt_text": "Свитшот RYOMEN SUKUNA — фото 3",
                        "is_main": False,
                        "sort_order": 20,
                    },
                ],
            },
            {
                "slug": "tokyo-team-tee",
                "name": "Футболка | TOKYO TEAM",
                "category": categories["tshirts"],
                "franchise": franchises["jujutsu-kaisen"],
                "description": (
                    "Лёгкая унисекс футболка с винтажным эффектом старения и потёртости. "
                    "Стирка до 30°C в деликатном режиме, срок производства: от 30 дней."
                ),
                "base_price": Decimal("5100.00"),
                "is_featured": False,
                "variants": [
                    ("AA-TTT-BLK-S", ProductVariant.Size.S, "Чёрный", 8),
                    ("AA-TTT-BLK-M", ProductVariant.Size.M, "Чёрный", 10),
                    ("AA-TTT-BLK-L", ProductVariant.Size.L, "Чёрный", 8),
                ],
                "images": [
                    {
                        "filename": "14-1 TOKYO TEAM.webp",
                        "alt_text": "Футболка TOKYO TEAM — фото 1",
                        "is_main": True,
                        "sort_order": 0,
                    },
                    {
                        "filename": "14-2 TOKYO TEAM.webp",
                        "alt_text": "Футболка TOKYO TEAM — фото 2",
                        "is_main": False,
                        "sort_order": 10,
                    },
                ],
            },
        ]

        for item in products:
            variants = item.pop("variants")
            images = item.pop("images", [])
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

            for image_spec in images:
                if product.images.filter(alt_text=image_spec["alt_text"]).exists():
                    product.images.filter(alt_text=image_spec["alt_text"]).update(
                        is_main=image_spec["is_main"],
                        sort_order=image_spec["sort_order"],
                        is_approved=True,
                    )
                    continue

                uploaded = self._load_stock_image(image_spec["filename"])
                if not uploaded:
                    continue
                ProductImage.objects.create(
                    product=product,
                    image=uploaded,
                    alt_text=image_spec["alt_text"],
                    is_main=image_spec["is_main"],
                    sort_order=image_spec["sort_order"],
                    is_approved=True,
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
