import pytest

from catalog.models import ProductVariant


pytestmark = pytest.mark.django_db


def test_user_can_store_and_clear_fit_profile(authenticated_client, user):
    empty_response = authenticated_client.get("/api/v1/users/me/fit-profile/")

    assert empty_response.status_code == 200
    assert empty_response.data["height_cm"] is None
    assert empty_response.data["tops_usual_size"] is None
    assert empty_response.data["is_complete"] is False

    update_response = authenticated_client.patch(
        "/api/v1/users/me/fit-profile/",
        {
            "height_cm": 178,
            "weight_kg": "74.5",
            "chest_cm": 101,
            "waist_cm": 86,
            "preferred_fit": "regular",
            "tops_usual_size": "M",
            "notes": "Usually prefer standard tees.",
        },
        format="json",
    )

    assert update_response.status_code == 200
    assert update_response.data["height_cm"] == 178
    assert update_response.data["weight_kg"] == "74.5"
    assert update_response.data["tops_usual_size"] == "M"
    assert update_response.data["is_complete"] is True
    assert update_response.data["updated_at"] is not None

    user.refresh_from_db()
    assert user.fit_profile["height_cm"] == 178
    assert user.fit_profile["weight_kg"] == "74.5"
    assert user.fit_profile_updated_at is not None

    clear_response = authenticated_client.patch(
        "/api/v1/users/me/fit-profile/",
        {"preferred_fit": None, "tops_usual_size": None, "notes": None},
        format="json",
    )

    assert clear_response.status_code == 200
    assert clear_response.data["preferred_fit"] is None
    assert clear_response.data["tops_usual_size"] is None
    assert clear_response.data["notes"] is None
    user.refresh_from_db()
    assert "preferred_fit" not in user.fit_profile
    assert "tops_usual_size" not in user.fit_profile
    assert "notes" not in user.fit_profile

    refreshed_response = authenticated_client.get("/api/v1/users/me/fit-profile/")

    assert refreshed_response.status_code == 200
    assert refreshed_response.data["is_complete"] is False


def test_product_detail_returns_deterministic_fit_recommendation(
    authenticated_client, user, product_factory
):
    user.update_fit_profile(
        {
            "height_cm": 180,
            "weight_kg": "76.0",
            "chest_cm": 100,
            "waist_cm": 84,
            "preferred_fit": "regular",
            "tops_usual_size": "M",
        }
    )

    product = product_factory(
        name="Fit Guided Hoodie",
        variants=[
            {
                "sku": "FIT-HOODIE-L",
                "size": ProductVariant.Size.L,
                "color": "Black",
                "stock_quantity": 4,
                "is_active": True,
            },
            {
                "sku": "FIT-HOODIE-XL",
                "size": ProductVariant.Size.XL,
                "color": "Black",
                "stock_quantity": 2,
                "is_active": True,
            },
        ],
    )

    response = authenticated_client.get(f"/api/v1/products/{product.slug}/")

    assert response.status_code == 200
    recommendation = response.data["fit_recommendation"]
    assert recommendation["recommended_size"] == "L"
    assert recommendation["confidence"] == "medium"
    assert "closest_available_size_selected" in recommendation["warnings"]
    assert "размер M" in recommendation["explanation"]


def test_product_detail_returns_default_fit_recommendation_for_anonymous_user(
    api_client, product_factory
):
    product = product_factory(name="Anonymous Fit Tee")

    response = api_client.get(f"/api/v1/products/{product.slug}/")

    assert response.status_code == 200
    recommendation = response.data["fit_recommendation"]
    assert recommendation["recommended_size"] is None
    assert recommendation["confidence"] == "none"
    assert recommendation["profile_ready"] is False
    assert recommendation["warnings"] == ["fit_profile_incomplete"]
