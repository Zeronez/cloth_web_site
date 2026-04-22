import importlib
import sys

import pytest


MODULE_NAME = "config.settings.production"


def _load_production_settings():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def _set_required_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://animeattire:secret@db:5432/animeattire"
    )
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.animeattire.example")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "https://animeattire.example")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://animeattire.example")


def test_production_settings_fail_without_secret_key(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _load_production_settings()


def test_production_settings_rejects_wildcard_hosts(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")
    monkeypatch.setenv("ALLOWED_HOSTS", "*")

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        _load_production_settings()


def test_production_settings_loads_with_explicit_contract(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")
    monkeypatch.setenv(
        "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
    )

    settings_module = _load_production_settings()

    assert settings_module.DEBUG is False
    assert settings_module.ALLOWED_HOSTS == ["api.animeattire.example"]
    assert settings_module.CSRF_TRUSTED_ORIGINS == ["https://animeattire.example"]
    assert settings_module.CORS_ALLOWED_ORIGINS == ["https://animeattire.example"]
    assert settings_module.SECURE_SSL_REDIRECT is True
