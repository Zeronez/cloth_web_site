import importlib
import sys

import pytest


MODULE_NAME = "config.settings.production"
STRONG_SECRET_KEY = "animeattire-production-secret-key-2026-with-64-characters"
WEBHOOK_SECRET = "yookassa-webhook-secret-with-at-least-32-chars"


def _load_production_settings():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def _set_required_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://animeattire:secret@postgres.internal:5432/animeattire",
    )
    monkeypatch.setenv("REDIS_URL", "redis://redis.internal:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://redis.internal:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://redis.internal:6379/2")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.animeattire.ru")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "https://animeattire.ru")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://animeattire.ru")
    monkeypatch.setenv("PAYMENT_WEBHOOK_BYPASS_PROVIDERS", "")
    monkeypatch.setenv(
        "PAYMENT_WEBHOOK_SECRETS_JSON",
        f'{{"yookassa":"{WEBHOOK_SECRET}"}}',
    )
    monkeypatch.setenv(
        "PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON",
        '{"yookassa":"https://checkout.animeattire.ru/yookassa"}',
    )
    monkeypatch.setenv(
        "PAYMENT_PROVIDER_RETURN_BASE_URL",
        "https://animeattire.ru/checkout/return",
    )
    monkeypatch.setenv("PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON", "{}")
    monkeypatch.setenv("DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON", "{}")


@pytest.mark.parametrize(
    "name",
    (
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "CORS_ALLOWED_ORIGINS",
        "PAYMENT_PROVIDER_RETURN_BASE_URL",
    ),
)
def test_production_settings_fail_without_required_env(monkeypatch, name):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match=name):
        _load_production_settings()


def test_production_settings_fail_without_secret_key(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _load_production_settings()


def test_production_settings_rejects_wildcard_hosts(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.setenv("ALLOWED_HOSTS", "*")

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        _load_production_settings()


@pytest.mark.parametrize(
    ("env_name", "env_value", "error_match"),
    (
        ("SECRET_KEY", "prod-secret-key", "SECRET_KEY"),
        ("DATABASE_URL", "sqlite:///db.sqlite3", "DATABASE_URL"),
        (
            "DATABASE_URL",
            "postgresql://animeattire@postgres.internal:5432/animeattire",
            "DATABASE_URL",
        ),
        ("REDIS_URL", "redis://localhost:6379/0", "REDIS_URL"),
        ("CELERY_BROKER_URL", "redis://localhost:6379/1", "CELERY_BROKER_URL"),
        ("ALLOWED_HOSTS", "https://api.animeattire.ru", "ALLOWED_HOSTS"),
        ("CSRF_TRUSTED_ORIGINS", "http://animeattire.ru", "CSRF_TRUSTED_ORIGINS"),
        ("CORS_ALLOWED_ORIGINS", "https://localhost", "CORS_ALLOWED_ORIGINS"),
        (
            "PAYMENT_WEBHOOK_BYPASS_PROVIDERS",
            "manual,placeholder",
            "PAYMENT_WEBHOOK_BYPASS_PROVIDERS",
        ),
        ("PAYMENT_WEBHOOK_SECRETS_JSON", "{}", "PAYMENT_WEBHOOK_SECRETS_JSON"),
        (
            "PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON",
            '{"yookassa":"https://yookassa.example/checkout"}',
            "PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON",
        ),
        (
            "PAYMENT_PROVIDER_RETURN_BASE_URL",
            "http://localhost:3000/checkout/return",
            "PAYMENT_PROVIDER_RETURN_BASE_URL",
        ),
        (
            "PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON",
            '{"external-1":{"status":"succeeded"}}',
            "PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON",
        ),
        (
            "DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON",
            '{"SHIP-1":{"status":"delivered"}}',
            "DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON",
        ),
    ),
)
def test_production_settings_rejects_unsafe_required_config(
    monkeypatch, env_name, env_value, error_match
):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(RuntimeError, match=error_match):
        _load_production_settings()


def test_production_settings_requires_smtp_credentials_when_smtp_enabled(
    monkeypatch,
):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    monkeypatch.setenv("EMAIL_HOST", "smtp.animeattire.ru")
    monkeypatch.setenv("EMAIL_HOST_USER", "mailer")
    monkeypatch.delenv("EMAIL_HOST_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="EMAIL_HOST_PASSWORD"):
        _load_production_settings()


def test_production_settings_requires_complete_s3_credentials_when_enabled(
    monkeypatch,
):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "animeattire-media")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "media-access-key")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(RuntimeError, match="AWS_SECRET_ACCESS_KEY"):
        _load_production_settings()


def test_non_production_settings_do_not_require_production_env(monkeypatch):
    for name in (
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "CORS_ALLOWED_ORIGINS",
        "PAYMENT_PROVIDER_RETURN_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    sys.modules.pop("config.settings.test", None)
    settings_module = importlib.import_module("config.settings.test")

    assert (
        settings_module.SECRET_KEY
        == "animeattire-test-secret-key-with-enough-entropy-for-hmac"
    )


def test_production_settings_loads_with_explicit_contract(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)
    monkeypatch.setenv(
        "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
    )

    settings_module = _load_production_settings()

    assert settings_module.DEBUG is False
    assert settings_module.ALLOWED_HOSTS == ["api.animeattire.ru"]
    assert settings_module.CSRF_TRUSTED_ORIGINS == ["https://animeattire.ru"]
    assert settings_module.CORS_ALLOWED_ORIGINS == ["https://animeattire.ru"]
    assert settings_module.PAYMENT_WEBHOOK_BYPASS_PROVIDERS == []
    assert settings_module.PAYMENT_WEBHOOK_SECRETS["yookassa"] == WEBHOOK_SECRET
    assert settings_module.SECURE_SSL_REDIRECT is True
