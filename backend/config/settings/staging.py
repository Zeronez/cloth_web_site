from urllib.parse import urlparse

import dj_database_url

from config.settings.base import *  # noqa: F403
from config.settings.env import env_bool, env_csv, env_int, env_required, env_value


def _require_non_empty(name, value):
    if not value:
        raise RuntimeError(f"{name} must be set in staging")


def _validate_database_url(value):
    parsed = urlparse(value)
    if not parsed.scheme.startswith("postgres"):
        raise RuntimeError("DATABASE_URL must use a PostgreSQL scheme in staging")
    if not parsed.hostname:
        raise RuntimeError("DATABASE_URL must include a hostname in staging")


def _validate_redis_url(name, value):
    parsed = urlparse(value)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise RuntimeError(f"{name} must use redis:// or rediss:// in staging")


def _validate_hosts(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in staging")
    for host in values:
        if "*" in host:
            raise RuntimeError(f"{name} cannot include wildcard hosts in staging")
        if "://" in host:
            raise RuntimeError(f"{name} must list hostnames without URL schemes")


def _validate_http_origins(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in staging")
    for origin in values:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"{name} entries must be absolute URLs in staging")


DEBUG = False
SECRET_KEY = env_required("SECRET_KEY")
DATABASE_URL = env_required("DATABASE_URL")
REDIS_URL = env_required("REDIS_URL")
CELERY_BROKER_URL = env_required("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env_required("CELERY_RESULT_BACKEND")
ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_csv("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS")

STAGING_PUBLIC_BASE_URL = env_required("STAGING_PUBLIC_BASE_URL")
STAGING_RESTORE_DRILL_ENABLED = env_bool("STAGING_RESTORE_DRILL_ENABLED", False)
STAGING_MEDIA_BUCKET = env_value("STAGING_MEDIA_BUCKET", "")
STAGING_MEDIA_BACKUP_PREFIX = env_value("STAGING_MEDIA_BACKUP_PREFIX", "backups/media")
STAGING_DATABASE_BACKUP_PREFIX = env_value(
    "STAGING_DATABASE_BACKUP_PREFIX", "backups/postgres"
)
STAGING_RESTORE_MAX_AGE_HOURS = env_int("STAGING_RESTORE_MAX_AGE_HOURS", 72)
AWS_STORAGE_BUCKET_NAME = env_value("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = env_value("AWS_S3_ENDPOINT_URL", "")
AWS_ACCESS_KEY_ID = env_value("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = env_value("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_REGION_NAME = env_value("AWS_S3_REGION_NAME", "us-east-1")

_require_non_empty("SECRET_KEY", SECRET_KEY)
_validate_database_url(DATABASE_URL)
_validate_redis_url("REDIS_URL", REDIS_URL)
_validate_redis_url("CELERY_BROKER_URL", CELERY_BROKER_URL)
_validate_redis_url("CELERY_RESULT_BACKEND", CELERY_RESULT_BACKEND)
_validate_hosts("ALLOWED_HOSTS", ALLOWED_HOSTS)
_validate_http_origins("CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS)
_validate_http_origins("CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS)
_require_non_empty("STAGING_PUBLIC_BASE_URL", STAGING_PUBLIC_BASE_URL)
if STAGING_RESTORE_MAX_AGE_HOURS < 1:
    raise RuntimeError("STAGING_RESTORE_MAX_AGE_HOURS must be >= 1 in staging")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=300,
        conn_health_checks=True,
    )
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 60 * 60)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
