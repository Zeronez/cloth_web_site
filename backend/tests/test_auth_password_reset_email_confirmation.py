from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest


pytestmark = pytest.mark.django_db


def clear_outbox():
    if hasattr(mail, "outbox"):
        mail.outbox.clear()
    else:
        mail.outbox = []


def make_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def test_register_queues_email_confirmation_message(
    api_client, django_capture_on_commit_callbacks
):
    clear_outbox()

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "username": "confirm-me",
                "email": "confirm@example.com",
                "password": "GhibliMerch!2026",
                "first_name": "Confirm",
                "last_name": "Me",
            },
            format="json",
        )

    assert response.status_code == 201
    user = get_user_model().objects.get(username="confirm-me")
    assert user.is_email_verified is False
    assert len(mail.outbox) == 1
    assert "подтвердите email" in mail.outbox[0].subject.lower()
    assert "confirm-email" in mail.outbox[0].body


def test_email_confirmation_confirm_marks_user_verified(api_client, user):
    uid = make_uid(user)
    token = default_token_generator.make_token(user)

    response = api_client.post(
        "/api/v1/auth/email-confirmation/confirm/",
        {"uid": uid, "token": token},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_email_verified is True
    assert response.data["is_email_verified"] is True


def test_email_confirmation_rejects_invalid_token(api_client, user):
    response = api_client.post(
        "/api/v1/auth/email-confirmation/confirm/",
        {"uid": make_uid(user), "token": "bad-token"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    user.refresh_from_db()
    assert user.is_email_verified is False


def test_authenticated_user_can_request_email_confirmation_resend(
    authenticated_client, user, django_capture_on_commit_callbacks
):
    clear_outbox()

    with django_capture_on_commit_callbacks(execute=True):
        response = authenticated_client.post(
            "/api/v1/auth/email-confirmation/request/",
            format="json",
        )

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to


def test_password_reset_request_sends_email_for_known_user(
    api_client, user, django_capture_on_commit_callbacks
):
    clear_outbox()

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": user.email},
            format="json",
        )

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert "восстановление пароля" in mail.outbox[0].subject.lower()
    assert "reset-password" in mail.outbox[0].body


def test_password_reset_request_does_not_leak_unknown_email(
    api_client, django_capture_on_commit_callbacks
):
    clear_outbox()

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": "missing@example.com"},
            format="json",
        )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


def test_password_reset_confirm_updates_password_and_allows_login(api_client, user):
    uid = make_uid(user)
    token = default_token_generator.make_token(user)

    confirm_response = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password": "FreshAnimePass!2026",
        },
        format="json",
    )
    login_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "FreshAnimePass!2026"},
        format="json",
    )

    assert confirm_response.status_code == 200
    assert login_response.status_code == 200
    assert "access" in login_response.data


def test_password_reset_confirm_rejects_invalid_token(api_client, user):
    response = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": make_uid(user),
            "token": "bad-token",
            "new_password": "FreshAnimePass!2026",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
