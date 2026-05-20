import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product, ProductVariant


class Command(BaseCommand):
    help = "Export products and variants to CSV files."

    def add_arguments(self, parser):
        parser.add_argument("--products", required=True, help="Path to products CSV")
        parser.add_argument("--variants", required=True, help="Path to variants CSV")

    def handle(self, *args, **options):
        products_path = Path(options["products"])
        variants_path = Path(options["variants"])

        if products_path.resolve() == variants_path.resolve():
            raise CommandError("--products and --variants must be different files.")

        products_path.parent.mkdir(parents=True, exist_ok=True)
        variants_path.parent.mkdir(parents=True, exist_ok=True)

        products = (
            Product.objects.select_related("category", "franchise")
            .prefetch_related("tags", "collections")
            .order_by("id")
        )
        variants = ProductVariant.objects.select_related("product").order_by("id")

        with products_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "id",
                    "name",
                    "slug",
                    "category_slug",
                    "franchise_slug",
                    "description",
                    "base_price",
                    "status",
                    "is_featured",
                    "search_synonyms",
                    "material",
                    "fit",
                    "care",
                    "gender",
                    "season",
                    "weight_grams",
                    "seo_title",
                    "seo_description",
                    "canonical_url",
                    "og_image_url",
                    "tags",
                    "collections",
                ],
            )
            writer.writeheader()
            for product in products:
                writer.writerow(
                    {
                        "id": product.id,
                        "name": product.name,
                        "slug": product.slug,
                        "category_slug": product.category.slug,
                        "franchise_slug": (
                            product.franchise.slug if product.franchise_id else ""
                        ),
                        "description": product.description,
                        "base_price": str(product.base_price),
                        "status": product.status,
                        "is_featured": "1" if product.is_featured else "0",
                        "search_synonyms": product.search_synonyms,
                        "material": product.material,
                        "fit": product.fit,
                        "care": product.care,
                        "gender": product.gender,
                        "season": product.season,
                        "weight_grams": product.weight_grams or "",
                        "seo_title": product.seo_title,
                        "seo_description": product.seo_description,
                        "canonical_url": product.canonical_url,
                        "og_image_url": product.og_image_url,
                        "tags": ",".join(tag.slug for tag in product.tags.all()),
                        "collections": ",".join(
                            collection.slug for collection in product.collections.all()
                        ),
                    }
                )

        with variants_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "id",
                    "product_id",
                    "sku",
                    "size",
                    "color",
                    "stock_quantity",
                    "price_delta",
                    "is_active",
                ],
            )
            writer.writeheader()
            for variant in variants:
                writer.writerow(
                    {
                        "id": variant.id,
                        "product_id": variant.product_id,
                        "sku": variant.sku,
                        "size": variant.size,
                        "color": variant.color,
                        "stock_quantity": variant.stock_quantity,
                        "price_delta": str(variant.price_delta),
                        "is_active": "1" if variant.is_active else "0",
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {products.count()} products to {products_path} and {variants.count()} variants to {variants_path}."
            )
        )
