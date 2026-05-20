import pytest


pytestmark = pytest.mark.django_db


def test_phone_confirmation_request_and_confirm_marks_user_verified(
    authenticated_client, user, settings
):
    settings.AUTH_PHONE_CONFIRMATION_TEST_CODE = "123456"

    request_response = authenticated_client.post(
        "/api/v1/auth/phone-confirmation/request/",
        {"phone": "+79990001122"},
        format="json",
    )
    confirm_response = authenticated_client.post(
        "/api/v1/auth/phone-confirmation/confirm/",
        {"code": "123456"},
        format="json",
    )

    assert request_response.status_code == 202
    assert confirm_response.status_code == 200
    user.refresh_from_db()
    assert user.phone == "+79990001122"
    assert user.is_phone_verified is True
    assert confirm_response.data["is_phone_verified"] is True


def test_phone_confirmation_rejects_invalid_code(authenticated_client, user, settings):
    settings.AUTH_PHONE_CONFIRMATION_TEST_CODE = "999000"

    request_response = authenticated_client.post(
        "/api/v1/auth/phone-confirmation/request/",
        {"phone": "+79990001122"},
        format="json",
    )
    confirm_response = authenticated_client.post(
        "/api/v1/auth/phone-confirmation/confirm/",
        {"code": "000000"},
        format="json",
    )

    assert request_response.status_code == 202
    assert confirm_response.status_code == 400
    assert confirm_response.data["error"]["code"] == "validation_error"
    user.refresh_from_db()
    assert user.is_phone_verified is False

