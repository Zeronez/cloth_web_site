import pytest


pytestmark = pytest.mark.django_db


def test_registration_requires_required_consents(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "consent-shopper",
            "email": "consent@example.com",
            "password": "GhibliMerch!2026",
            "first_name": "Consent",
            "last_name": "Shopper",
            "phone": "+79991234567",
            "privacy_policy_accepted": False,
            "offer_agreement_accepted": False,
            "marketing_opt_in": False,
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"


def test_registration_persists_required_consents_and_optional_marketing(
    api_client, settings
):
    settings.PRIVACY_POLICY_VERSION = "2026-05-privacy"
    settings.OFFER_AGREEMENT_VERSION = "2026-05-offer"
    settings.MARKETING_CONSENT_VERSION = "2026-05-marketing"

    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "consented-shopper",
            "email": "consented@example.com",
            "password": "GhibliMerch!2026",
            "first_name": "Consented",
            "last_name": "Shopper",
            "phone": "+79991234567",
            "privacy_policy_accepted": True,
            "offer_agreement_accepted": True,
            "marketing_opt_in": True,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["has_accepted_privacy_policy"] is True
    assert response.data["privacy_policy_version"] == "2026-05-privacy"
    assert response.data["has_accepted_offer_agreement"] is True
    assert response.data["offer_agreement_version"] == "2026-05-offer"
    assert response.data["is_marketing_subscribed"] is True
    assert response.data["marketing_opt_in_version"] == "2026-05-marketing"


def test_user_can_toggle_marketing_subscription_from_profile(
    authenticated_client, user, settings
):
    settings.MARKETING_CONSENT_VERSION = "2026-06-marketing"

    subscribe_response = authenticated_client.patch(
        "/api/v1/users/me/",
        {"is_marketing_subscribed": True},
        format="json",
    )
    unsubscribe_response = authenticated_client.patch(
        "/api/v1/users/me/",
        {"is_marketing_subscribed": False},
        format="json",
    )

    assert subscribe_response.status_code == 200
    assert subscribe_response.data["is_marketing_subscribed"] is True
    assert subscribe_response.data["marketing_opt_in_version"] == "2026-06-marketing"

    assert unsubscribe_response.status_code == 200
    assert unsubscribe_response.data["is_marketing_subscribed"] is False
    assert unsubscribe_response.data["marketing_opt_in_version"] == ""
