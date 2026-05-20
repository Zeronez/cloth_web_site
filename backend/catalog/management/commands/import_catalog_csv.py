import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductCollection,
    ProductTag,
    ProductVariant,
)


class Command(BaseCommand):
    help = "Import products and variants from CSV files (id-based updates; creates when missing)."

    def add_arguments(self, parser):
        parser.add_argument("--products", required=True, help="Path to products CSV")
        parser.add_argument("--variants", required=True, help="Path to variants CSV")

    def handle(self, *args, **options):
        products_path = Path(options["products"])
        variants_path = Path(options["variants"])
        if not products_path.exists():
            raise CommandError(f"Products file not found: {products_path}")
        if not variants_path.exists():
            raise CommandError(f"Variants file not found: {variants_path}")

        with transaction.atomic():
            products_by_id = {}
            with products_path.open("r", newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    product_id = int(row["id"]) if row.get("id") else None
                    if not product_id:
                        raise CommandError("Products CSV requires non-empty id column.")

                    category = Category.objects.get(slug=row["category_slug"])
                    franchise_slug = (row.get("franchise_slug") or "").strip()
                    franchise = (
                        AnimeFranchise.objects.get(slug=franchise_slug)
                        if franchise_slug
                        else None
                    )

                    defaults = {
                        "category": category,
                        "franchise": franchise,
                        "name": row["name"],
                        "slug": row["slug"],
                        "description": row.get("description") or "",
                        "base_price": Decimal(row["base_price"]),
                        "status": row.get("status") or Product.PublishingStatus.ACTIVE,
                        "is_featured": row.get("is_featured") in {"1", "true", "True"},
                        "search_synonyms": row.get("search_synonyms") or "",
                        "material": row.get("material") or "",
                        "fit": row.get("fit") or "",
                        "care": row.get("care") or "",
                        "gender": row.get("gender") or "",
                        "season": row.get("season") or "",
                        "weight_grams": int(row["weight_grams"])
                        if (row.get("weight_grams") or "").strip()
                        else None,
                        "seo_title": row.get("seo_title") or "",
                        "seo_description": row.get("seo_description") or "",
                        "canonical_url": row.get("canonical_url") or "",
                        "og_image_url": row.get("og_image_url") or "",
                    }

                    product, _created = Product.objects.update_or_create(
                        id=product_id,
                        defaults=defaults,
                    )

                    tags = [
                        slug.strip()
                        for slug in (row.get("tags") or "").split(",")
                        if slug.strip()
                    ]
                    collections = [
                        slug.strip()
                        for slug in (row.get("collections") or "").split(",")
                        if slug.strip()
                    ]
                    if tags:
                        tag_objs = []
                        for slug in tags:
                            tag, _ = ProductTag.objects.get_or_create(
                                slug=slug, defaults={"name": slug.replace("-", " ")}
                            )
                            tag_objs.append(tag)
                        product.tags.set(tag_objs)
                    if collections:
                        col_objs = []
                        for slug in collections:
                            col, _ = ProductCollection.objects.get_or_create(
                                slug=slug, defaults={"name": slug.replace("-", " ")}
                            )
                            col_objs.append(col)
                        product.collections.set(col_objs)

                    products_by_id[product.id] = product

            with variants_path.open("r", newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    variant_id = int(row["id"]) if row.get("id") else None
                    product_id = int(row["product_id"])
                    if not variant_id:
                        raise CommandError("Variants CSV requires non-empty id column.")
                    if product_id not in products_by_id and not Product.objects.filter(
                        id=product_id
                    ).exists():
                        raise CommandError(
                            f"Variant references unknown product_id={product_id}."
                        )

                    ProductVariant.objects.update_or_create(
                        id=variant_id,
                        defaults={
                            "product_id": product_id,
                            "sku": row["sku"],
                            "size": row["size"],
                            "color": row["color"],
                            "stock_quantity": int(row.get("stock_quantity") or 0),
                            "price_delta": Decimal(row.get("price_delta") or "0"),
                            "is_active": row.get("is_active") in {"1", "true", "True"},
                        },
                    )

        self.stdout.write(self.style.SUCCESS("Import completed."))

