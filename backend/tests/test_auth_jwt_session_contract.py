import pytest
from django.contrib.auth import get_user_model


pytestmark = pytest.mark.django_db


def login(api_client, username, password):
    response = api_client.post(
        "/api/v1/auth/token/",
        {"username": username, "password": password},
        format="json",
    )
    assert response.status_code == 200
    return response.data


def create_user(username, password="GhibliMerch!2026"):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )


def test_refresh_rotation_blacklists_previous_refresh_token(api_client):
    create_user("rotation-shopper")
    tokens = login(api_client, "rotation-shopper", "GhibliMerch!2026")

    refresh_response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert refresh_response.status_code == 200
    assert refresh_response.data["access"]
    assert refresh_response.data["refresh"]
    assert refresh_response.data["refresh"] != tokens["refresh"]

    old_refresh_response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert old_refresh_response.status_code == 401


def test_logout_blacklists_refresh_token(api_client):
    create_user("logout-shopper")
    tokens = login(api_client, "logout-shopper", "GhibliMerch!2026")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    logout_response = api_client.post(
        "/api/v1/auth/logout/",
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert logout_response.status_code == 204

    refresh_response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert refresh_response.status_code == 401


def test_logout_rejects_missing_malformed_and_foreign_refresh_tokens(api_client):
    create_user("session-owner")
    create_user("other-session")
    owner_tokens = login(api_client, "session-owner", "GhibliMerch!2026")
    other_tokens = login(api_client, "other-session", "GhibliMerch!2026")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {owner_tokens['access']}")

    missing_response = api_client.post("/api/v1/auth/logout/", {}, format="json")
    assert missing_response.status_code == 400

    malformed_response = api_client.post(
        "/api/v1/auth/logout/",
        {"refresh": "not-a-refresh-token"},
        format="json",
    )
    assert malformed_response.status_code == 400

    foreign_response = api_client.post(
        "/api/v1/auth/logout/",
        {"refresh": other_tokens["refresh"]},
        format="json",
    )
    assert foreign_response.status_code == 400

    still_valid_response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": other_tokens["refresh"]},
        format="json",
    )
    assert still_valid_response.status_code == 200


def test_auth_endpoints_do_not_issue_browser_cookies(api_client):
    create_user("cookie-free-shopper")

    token_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": "cookie-free-shopper", "password": "GhibliMerch!2026"},
        format="json",
    )

    assert token_response.status_code == 200
    assert "Set-Cookie" not in token_response
    assert token_response.cookies == {}
