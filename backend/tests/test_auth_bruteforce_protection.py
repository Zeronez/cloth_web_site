from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def auth_bruteforce_settings(settings):
    settings.AUTH_LOGIN_FAILURE_WINDOW_SECONDS = 900
    settings.AUTH_LOGIN_FAILURE_IP_LIMIT = 2
    settings.AUTH_LOGIN_FAILURE_ACCOUNT_LIMIT = 2
    settings.AUTH_PASSWORD_RESET_REQUEST_WINDOW_SECONDS = 3600
    settings.AUTH_PASSWORD_RESET_REQUEST_LIMIT = 2
    settings.AUTH_PASSWORD_RESET_CONFIRM_WINDOW_SECONDS = 3600
    settings.AUTH_PASSWORD_RESET_CONFIRM_LIMIT = 2
    cache.clear()
    yield
    cache.clear()


def clear_outbox():
    if hasattr(mail, "outbox"):
        mail.outbox.clear()
    else:
        mail.outbox = []


def make_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def test_login_failures_across_ips_lock_same_username_bucket(api_client, user):
    payload = {"username": user.username, "password": "wrong-password"}

    first = api_client.post(
        "/api/v1/auth/token/",
        payload,
        format="json",
        REMOTE_ADDR="198.51.100.10",
    )
    second = api_client.post(
        "/api/v1/auth/token/",
        payload,
        format="json",
        REMOTE_ADDR="198.51.100.11",
    )
    throttled = api_client.post(
        "/api/v1/auth/token/",
        payload,
        format="json",
        REMOTE_ADDR="198.51.100.12",
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert throttled.status_code == 429
    assert throttled.data["error"]["code"] == "throttled"


def test_successful_login_clears_failure_counters(api_client, user):
    wrong_payload = {"username": user.username, "password": "wrong-password"}
    correct_payload = {"username": user.username, "password": "GhibliMerch!2026"}

    wrong = api_client.post(
        "/api/v1/auth/token/",
        wrong_payload,
        format="json",
        REMOTE_ADDR="198.51.100.20",
    )
    success = api_client.post(
        "/api/v1/auth/token/",
        correct_payload,
        format="json",
        REMOTE_ADDR="198.51.100.20",
    )
    next_wrong = api_client.post(
        "/api/v1/auth/token/",
        wrong_payload,
        format="json",
        REMOTE_ADDR="198.51.100.20",
    )

    assert wrong.status_code == 401
    assert success.status_code == 200
    assert "access" in success.data
    assert next_wrong.status_code == 401


def test_password_reset_request_is_suppressed_after_limit(
    api_client, user, django_capture_on_commit_callbacks
):
    clear_outbox()

    with django_capture_on_commit_callbacks(execute=True):
        first = api_client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": user.email},
            format="json",
        )
        second = api_client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": user.email.upper()},
            format="json",
        )
        third = api_client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": user.email},
            format="json",
        )

    assert first.status_code == 202
    assert second.status_code == 202
    assert third.status_code == 202
    assert len(mail.outbox) == 2


def test_password_reset_confirm_throttles_repeated_invalid_tokens(api_client, user):
    payload = {
        "uid": make_uid(user),
        "token": "bad-token",
        "new_password": "FreshAnimePass!2026",
    }

    first = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        payload,
        format="json",
        REMOTE_ADDR="203.0.113.50",
    )
    second = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        payload,
        format="json",
        REMOTE_ADDR="203.0.113.50",
    )
    throttled = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        payload,
        format="json",
        REMOTE_ADDR="203.0.113.50",
    )

    assert first.status_code == 400
    assert second.status_code == 400
    assert throttled.status_code == 429
    assert throttled.data["error"]["code"] == "throttled"


def test_password_reset_confirm_success_clears_failure_counter(api_client, user):
    uid = make_uid(user)
    wrong_payload = {
        "uid": uid,
        "token": "bad-token",
        "new_password": "FreshAnimePass!2026",
    }
    valid_payload = {
        "uid": uid,
        "token": default_token_generator.make_token(user),
        "new_password": "FreshAnimePass!2026",
    }

    wrong = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        wrong_payload,
        format="json",
        REMOTE_ADDR="203.0.113.60",
    )
    success = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        valid_payload,
        format="json",
        REMOTE_ADDR="203.0.113.60",
    )
    retry_wrong = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": uid,
            "token": "still-bad",
            "new_password": "AnotherAnimePass!2026",
        },
        format="json",
        REMOTE_ADDR="203.0.113.60",
    )

    assert wrong.status_code == 400
    assert success.status_code == 200
    assert retry_wrong.status_code == 400
