import importlib
import sys

import pytest


MODULE_NAME = "config.settings.staging"


def _load_staging_settings():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def _set_required_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://animeattire:secret@postgres:5432/animeattire_staging",
    )
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1,backend")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:3001")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3001")
    monkeypatch.setenv("STAGING_PUBLIC_BASE_URL", "http://localhost:3001")


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
        "STAGING_PUBLIC_BASE_URL",
    ),
)
def test_staging_settings_fail_without_required_env(monkeypatch, name):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "animeattire-staging-secret-key")
    monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match=name):
        _load_staging_settings()


@pytest.mark.parametrize(
    ("env_name", "env_value", "error_match"),
    (
        ("DATABASE_URL", "sqlite:///db.sqlite3", "DATABASE_URL"),
        ("REDIS_URL", "http://redis:6379/0", "REDIS_URL"),
        ("ALLOWED_HOSTS", "*", "ALLOWED_HOSTS"),
        ("ALLOWED_HOSTS", "https://backend", "ALLOWED_HOSTS"),
        ("CSRF_TRUSTED_ORIGINS", "localhost:3001", "CSRF_TRUSTED_ORIGINS"),
        ("CORS_ALLOWED_ORIGINS", "localhost:3001", "CORS_ALLOWED_ORIGINS"),
        ("STAGING_RESTORE_MAX_AGE_HOURS", "0", "STAGING_RESTORE_MAX_AGE_HOURS"),
    ),
)
def test_staging_settings_reject_unsafe_values(
    monkeypatch, env_name, env_value, error_match
):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "animeattire-staging-secret-key")
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(RuntimeError, match=error_match):
        _load_staging_settings()


def test_staging_settings_load_with_explicit_contract(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "animeattire-staging-secret-key")
    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "animeattire-staging-media")
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "minioadmin")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

    settings_module = _load_staging_settings()

    assert settings_module.DEBUG is False
    assert settings_module.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "backend"]
    assert settings_module.CSRF_TRUSTED_ORIGINS == ["http://localhost:3001"]
    assert settings_module.CORS_ALLOWED_ORIGINS == ["http://localhost:3001"]
    assert settings_module.STAGING_PUBLIC_BASE_URL == "http://localhost:3001"
    assert settings_module.STAGING_RESTORE_DRILL_ENABLED is False
    assert settings_module.STAGING_MEDIA_BUCKET == ""
    assert settings_module.STAGING_MEDIA_BACKUP_PREFIX == "backups/media"
    assert settings_module.STAGING_DATABASE_BACKUP_PREFIX == "backups/postgres"
    assert settings_module.STAGING_RESTORE_MAX_AGE_HOURS == 72
    assert settings_module.SESSION_COOKIE_SECURE is True
    assert settings_module.CSRF_COOKIE_SECURE is True
    assert settings_module.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings_module.X_FRAME_OPTIONS == "DENY"
    assert (
        settings_module.DEFAULT_FILE_STORAGE
        == "storages.backends.s3boto3.S3Boto3Storage"
    )
