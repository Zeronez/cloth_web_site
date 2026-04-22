from datetime import timedelta
from urllib.parse import urlparse

import dj_database_url

from config.settings.base import *  # noqa: F403
from config.settings.env import env_bool, env_csv, env_int, env_required, env_value


def _require_non_empty(name, value):
    if not value:
        raise RuntimeError(f"{name} must be set in production")


def _validate_database_url(value):
    parsed = urlparse(value)
    if not parsed.scheme.startswith("postgres"):
        raise RuntimeError("DATABASE_URL must use a PostgreSQL scheme in production")


def _validate_redis_url(name, value):
    parsed = urlparse(value)
    if parsed.scheme not in {"redis", "rediss"}:
        raise RuntimeError(f"{name} must use redis:// or rediss:// in production")


def _validate_hosts(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in production")
    if "*" in values:
        raise RuntimeError(f"{name} cannot include a wildcard host in production")


def _validate_http_origins(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in production")
    for origin in values:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(
                f"{name} entries must be absolute http or https URLs in production"
            )
        if (
            parsed.path not in {"", "/"}
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError(
                f"{name} entries must not include paths or query strings"
            )


def _validate_smtp_settings():
    if EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
        return
    _require_non_empty("EMAIL_HOST", EMAIL_HOST)
    _require_non_empty("EMAIL_PORT", str(EMAIL_PORT))
    _require_non_empty("EMAIL_HOST_USER", EMAIL_HOST_USER)
    _require_non_empty("EMAIL_HOST_PASSWORD", EMAIL_HOST_PASSWORD)


def _validate_s3_settings():
    if not (AWS_STORAGE_BUCKET_NAME or AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY):
        return
    _require_non_empty("AWS_STORAGE_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME)
    _require_non_empty("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
    _require_non_empty("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
    _require_non_empty("AWS_S3_REGION_NAME", AWS_S3_REGION_NAME)


DEBUG = False
SECRET_KEY = env_required("SECRET_KEY")
DATABASE_URL = env_required("DATABASE_URL")
REDIS_URL = env_required("REDIS_URL")
CELERY_BROKER_URL = env_required("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env_required("CELERY_RESULT_BACKEND")
ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_csv("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS")
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env_int("SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 30)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env_int("SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS", 14)
    ),
    "ROTATE_REFRESH_TOKENS": env_bool("SIMPLE_JWT_ROTATE_REFRESH_TOKENS", True),
    "BLACKLIST_AFTER_ROTATION": env_bool("SIMPLE_JWT_BLACKLIST_AFTER_ROTATION", True),
}
DEFAULT_FROM_EMAIL = env_value(
    "DEFAULT_FROM_EMAIL", "AnimeAttire <no-reply@example.com>"
)
SERVER_EMAIL = env_value("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_BACKEND = env_value(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env_value("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_value("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_value("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
AWS_STORAGE_BUCKET_NAME = env_value("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = env_value("AWS_S3_ENDPOINT_URL", "")
AWS_ACCESS_KEY_ID = env_value("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = env_value("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_REGION_NAME = env_value("AWS_S3_REGION_NAME", "us-east-1")

_validate_database_url(DATABASE_URL)
_validate_redis_url("REDIS_URL", REDIS_URL)
_validate_redis_url("CELERY_BROKER_URL", CELERY_BROKER_URL)
_validate_redis_url("CELERY_RESULT_BACKEND", CELERY_RESULT_BACKEND)
_validate_hosts("ALLOWED_HOSTS", ALLOWED_HOSTS)
_validate_http_origins("CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS)
_validate_http_origins("CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS)
_validate_smtp_settings()
_validate_s3_settings()

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
