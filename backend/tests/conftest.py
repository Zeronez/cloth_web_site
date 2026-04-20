from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import AnimeFranchise, Category, Product, ProductVariant


@pytest.fixture(autouse=True)
def api_test_settings(settings):
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "pytest",
        }
    }


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="shopper",
        email="shopper@example.com",
        password="GhibliMerch!2026",
        first_name="QA",
        last_name="Shopper",
    )


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(
        username="other-shopper",
        email="other@example.com",
        password="GhibliMerch!2026",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def product_factory(db):
    counters = {"category": 0, "franchise": 0, "product": 0, "variant": 0}

    def create_product(
        *,
        name=None,
        category=None,
        franchise=None,
        base_price="39.90",
        description="Premium anime streetwear made for daily use.",
        is_active=True,
        is_featured=False,
        variants=None,
    ):
        counters["product"] += 1
        if category is None:
            counters["category"] += 1
            category = Category.objects.create(name=f"Category {counters['category']}")
        if franchise is None:
            counters["franchise"] += 1
            franchise = AnimeFranchise.objects.create(
                name=f"Franchise {counters['franchise']}"
            )

        product = Product.objects.create(
            category=category,
            franchise=franchise,
            name=name or f"Product {counters['product']}",
            description=description,
            base_price=Decimal(base_price),
            is_active=is_active,
            is_featured=is_featured,
        )

        variant_specs = variants or [
            {
                "size": ProductVariant.Size.M,
                "color": "Black",
                "stock_quantity": 5,
                "price_delta": "0.00",
            }
        ]
        for spec in variant_specs:
            counters["variant"] += 1
            ProductVariant.objects.create(
                product=product,
                sku=spec.get("sku", f"SKU-{counters['variant']}"),
                size=spec.get("size", ProductVariant.Size.M),
                color=spec.get("color", "Black"),
                stock_quantity=spec.get("stock_quantity", 5),
                price_delta=Decimal(spec.get("price_delta", "0.00")),
                is_active=spec.get("is_active", True),
            )

        return product

    return create_product
