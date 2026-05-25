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
    assert recommendation["outfit"]["items"]
    assert Decimal(recommendation["outfit"]["total_price"]) >= Decimal(anchor.base_price)
