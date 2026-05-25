from decimal import Decimal

import pytest

from catalog.models import ProductRelation, ProductTag
from catalog.services import build_size_recommendation


pytestmark = pytest.mark.django_db


def test_build_size_recommendation_returns_profile_guidance_for_guest(product_factory):
    product = product_factory(name="Guest Recommendation Tee")

    class AnonymousUser:
        is_authenticated = False

    recommendation = build_size_recommendation(
        product=product,
        user=AnonymousUser(),
    )

    assert recommendation["recommended_size"] is None
    assert recommendation["profile_ready"] is False
    assert "fit_profile_incomplete" in recommendation["warnings"]


def test_build_size_recommendation_includes_outfit_and_style_warnings(
    user, product_factory
):
    anchor = product_factory(
        name="Berserk Oversized Hoodie",
        base_price="10000.00",
        description="Dark oversized hoodie for streetwear looks.",
        variants=[
            {"sku": "BERSERK-HOODIE-M", "size": "M", "color": "Black", "stock_quantity": 5},
            {"sku": "BERSERK-HOODIE-L", "size": "L", "color": "Black", "stock_quantity": 2},
        ],
    )
    anchor.fit = "oversized"
    anchor.season = "winter"
    anchor.save(update_fields=["fit", "season", "updated_at"])

    companion = product_factory(
        name="Berserk Cargo Pants",
        category=anchor.category,
        franchise=anchor.franchise,
        base_price="8000.00",
        description="Cargo pants for dark fantasy styling.",
    )
    accessory = product_factory(
        name="Berserk Layer Tee",
        base_price="3000.00",
        description="Layer tee for dark fantasy capsule outfits.",
        franchise=anchor.franchise,
    )

    ProductRelation.objects.create(from_product=anchor, to_product=accessory, sort_order=1)
    ProductRelation.objects.create(from_product=anchor, to_product=companion, sort_order=2)
    dark_tag = ProductTag.objects.create(name="Dark Fantasy", slug="dark-fantasy")
    anchor.tags.add(dark_tag)
    accessory.tags.add(dark_tag)

    user.update_fit_profile(
        {
            "height_cm": 176,
            "weight_kg": "72.0",
            "chest_cm": 100,
            "waist_cm": 84,
            "preferred_fit": "slim",
            "preferred_style": "minimal",
            "preferred_season": "summer",
            "tops_usual_size": "M",
            "budget_max_rub": 15000,
        }
    )

    recommendation = build_size_recommendation(product=anchor, user=user)

    assert recommendation["recommended_size"] in {"S", "M"}
    assert recommendation["profile_ready"] is True
    assert "style_fit_mismatch" in recommendation["warnings"]
    assert "season_mismatch" in recommendation["warnings"]
    assert recommendation["risk_level"] in {"medium", "high"}
    assert recommendation["risk_reasons"]
    assert recommendation["outfit"]["items"]
    assert Decimal(recommendation["outfit"]["total_price"]) >= Decimal(anchor.base_price)


def test_build_size_recommendation_uses_merch_metadata_and_budget_signal(
    user, product_factory
):
    product = product_factory(
        name="Metadata Hoodie",
        base_price="12000.00",
        variants=[
            {"sku": "META-HOODIE-S", "size": "S", "color": "Black", "stock_quantity": 5},
            {"sku": "META-HOODIE-M", "size": "M", "color": "Black", "stock_quantity": 5},
            {"sku": "META-HOODIE-L", "size": "L", "color": "Black", "stock_quantity": 5},
        ],
    )
    product.recommendation_fit_tendency = "runs_small"
    product.recommendation_notes = "Модель сидит плотнее обычного."
    product.recommendation_body_shape_notes = "Лучше подходит для многослойных образов."
    product.save(
        update_fields=[
            "recommendation_fit_tendency",
            "recommendation_notes",
            "recommendation_body_shape_notes",
            "updated_at",
        ]
    )
    companion = product_factory(
        name="Metadata Pants",
        franchise=product.franchise,
        base_price="9000.00",
    )
    ProductRelation.objects.create(from_product=product, to_product=companion, sort_order=1)

    user.update_fit_profile(
        {
            "height_cm": 176,
            "weight_kg": "69.0",
            "preferred_fit": "regular",
            "preferred_style": "streetwear",
            "tops_usual_size": "M",
            "budget_max_rub": 15000,
        }
    )

    recommendation = build_size_recommendation(product=product, user=user)

    assert recommendation["recommended_size"] == "L"
    assert "runs_small" in recommendation["warnings"]
    assert "Модель сидит плотнее обычного." in recommendation["explanation"]
    assert recommendation["outfit"]["budget_status"] in {"near_budget", "over_budget"}
    assert recommendation["outfit"]["budget_warning"]
