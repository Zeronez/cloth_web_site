from datetime import timedelta
from urllib.parse import urlparse

import dj_database_url

from config.settings.base import *  # noqa: F403
from config.settings.env import (
    env_bool,
    env_csv,
    env_int,
    env_json,
    env_required,
    env_value,
)


UNSAFE_SECRET_KEY_MARKERS = {
    "unsafe",
    "local",
    "dev",
    "test",
    "example",
    "change-me",
    "changeme",
    "prod-secret-key",
}

UNSAFE_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "example.com"}
UNSAFE_DOMAIN_SUFFIXES = (".example", ".example.com", ".test", ".local")
UNSAFE_WEBHOOK_BYPASS_PROVIDERS = {"manual", "placeholder", "local", "test"}


def _require_non_empty(name, value):
    if not value:
        raise RuntimeError(f"{name} must be set in production")


def _validate_secret_key(value):
    _require_non_empty("SECRET_KEY", value)
    normalized = value.lower()
    if len(value) < 50:
        raise RuntimeError("SECRET_KEY must be at least 50 characters in production")
    if any(marker in normalized for marker in UNSAFE_SECRET_KEY_MARKERS):
        raise RuntimeError("SECRET_KEY contains an unsafe marker for production")


def _validate_database_url(value):
    parsed = urlparse(value)
    if not parsed.scheme.startswith("postgres"):
        raise RuntimeError("DATABASE_URL must use a PostgreSQL scheme in production")
    if parsed.hostname in UNSAFE_HOSTNAMES:
        raise RuntimeError("DATABASE_URL cannot point at a local/example host")
    if not parsed.username or not parsed.password:
        raise RuntimeError("DATABASE_URL must include credentials in production")


def _validate_redis_url(name, value):
    parsed = urlparse(value)
    if parsed.scheme not in {"redis", "rediss"}:
        raise RuntimeError(f"{name} must use redis:// or rediss:// in production")
    if parsed.hostname in UNSAFE_HOSTNAMES:
        raise RuntimeError(f"{name} cannot point at a local/example host")


def _validate_hosts(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in production")
    for host in values:
        if "*" in host:
            raise RuntimeError(f"{name} cannot include a wildcard host in production")
        if "://" in host:
            raise RuntimeError(f"{name} must contain hostnames without URL schemes")
        _validate_public_hostname(name, host)


def _validate_http_origins(name, values):
    if not values:
        raise RuntimeError(f"{name} must be set in production")
    for origin in values:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(
                f"{name} entries must be absolute http or https URLs in production"
            )
        if parsed.scheme != "https":
            raise RuntimeError(f"{name} entries must use HTTPS in production")
        _validate_public_hostname(name, parsed.hostname)
        if (
            parsed.path not in {"", "/"}
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError(
                f"{name} entries must not include paths or query strings"
            )


def _validate_public_hostname(name, hostname):
    if not hostname:
        raise RuntimeError(f"{name} must include a hostname")
    if hostname in UNSAFE_HOSTNAMES or hostname.endswith(UNSAFE_DOMAIN_SUFFIXES):
        raise RuntimeError(f"{name} cannot use local, test, or example hosts")


def _validate_https_url(name, value):
    _require_non_empty(name, value)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(f"{name} must be an absolute HTTPS URL in production")
    _validate_public_hostname(name, parsed.hostname)


def _validate_positive_int(name, value, *, minimum=1):
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum} in production")


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
    if AWS_S3_REGION_NAME.lower() in {"example", "test", "local"}:
        raise RuntimeError("AWS_S3_REGION_NAME cannot be a placeholder")
    if AWS_S3_ENDPOINT_URL:
        _validate_https_url("AWS_S3_ENDPOINT_URL", AWS_S3_ENDPOINT_URL)


def _validate_payment_webhook_settings():
    unsafe_bypass = (
        set(PAYMENT_WEBHOOK_BYPASS_PROVIDERS) & UNSAFE_WEBHOOK_BYPASS_PROVIDERS
    )
    if unsafe_bypass:
        providers = ", ".join(sorted(unsafe_bypass))
        raise RuntimeError(
            f"PAYMENT_WEBHOOK_BYPASS_PROVIDERS cannot include {providers} in production"
        )
    if not PAYMENT_WEBHOOK_SECRETS:
        raise RuntimeError("PAYMENT_WEBHOOK_SECRETS_JSON must be set in production")
    for provider_code, secret in PAYMENT_WEBHOOK_SECRETS.items():
        if not str(secret).strip() or len(str(secret)) < 32:
            raise RuntimeError(
                f"Payment webhook secret for {provider_code} is too short"
            )
    for provider_code, url in PAYMENT_PROVIDER_CONFIRMATION_URLS.items():
        _validate_https_url(
            f"PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON[{provider_code}]", url
        )
    _validate_https_url(
        "PAYMENT_PROVIDER_RETURN_BASE_URL", PAYMENT_PROVIDER_RETURN_BASE_URL
    )


def _validate_no_sandbox_overrides():
    if PAYMENT_PROVIDER_STATUS_OVERRIDES:
        raise RuntimeError(
            "PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON must be empty in production"
        )
    if DELIVERY_PROVIDER_TRACKING_OVERRIDES:
        raise RuntimeError(
            "DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON must be empty in production"
        )


def _validate_celery_notification_settings():
    _require_non_empty("CELERY_NOTIFICATION_QUEUE", CELERY_NOTIFICATION_QUEUE)
    _validate_positive_int("CELERY_TASK_TIME_LIMIT", CELERY_TASK_TIME_LIMIT)
    _validate_positive_int(
        "CELERY_WORKER_PREFETCH_MULTIPLIER", CELERY_WORKER_PREFETCH_MULTIPLIER
    )
    _validate_positive_int(
        "CELERY_NOTIFICATION_MAX_RETRIES", CELERY_NOTIFICATION_MAX_RETRIES, minimum=0
    )
    _validate_positive_int(
        "CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS",
        CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS,
    )
    _validate_positive_int(
        "CELERY_NOTIFICATION_RETRY_MAX_SECONDS",
        CELERY_NOTIFICATION_RETRY_MAX_SECONDS,
    )
    _validate_positive_int(
        "CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS",
        CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS,
    )
    if (
        CELERY_NOTIFICATION_RETRY_MAX_SECONDS
        < CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS
    ):
        raise RuntimeError(
            "CELERY_NOTIFICATION_RETRY_MAX_SECONDS must be >= CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS in production"
        )
    if CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS < CELERY_TASK_TIME_LIMIT:
        raise RuntimeError(
            "CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS must be >= CELERY_TASK_TIME_LIMIT in production"
        )


def _validate_background_cleanup_settings():
    _validate_positive_int(
        "PAYMENT_SESSION_TIMEOUT_MINUTES", PAYMENT_SESSION_TIMEOUT_MINUTES
    )
    _validate_positive_int(
        "PAYMENT_EXPIRATION_BATCH_SIZE", PAYMENT_EXPIRATION_BATCH_SIZE
    )
    _validate_positive_int("CART_GUEST_TTL_HOURS", CART_GUEST_TTL_HOURS)
    _validate_positive_int("CART_CLEANUP_BATCH_SIZE", CART_CLEANUP_BATCH_SIZE)


DEBUG = False
SECRET_KEY = env_required("SECRET_KEY")
DATABASE_URL = env_required("DATABASE_URL")
REDIS_URL = env_required("REDIS_URL")
CELERY_BROKER_URL = env_required("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env_required("CELERY_RESULT_BACKEND")
CELERY_TASK_DEFAULT_QUEUE = env_value("CELERY_TASK_DEFAULT_QUEUE", "default")
CELERY_NOTIFICATION_QUEUE = env_value("CELERY_NOTIFICATION_QUEUE", "notifications")
CELERY_TASK_TIME_LIMIT = env_int("CELERY_TASK_TIME_LIMIT", 300)
CELERY_WORKER_PREFETCH_MULTIPLIER = env_int("CELERY_WORKER_PREFETCH_MULTIPLIER", 1)
CELERY_NOTIFICATION_MAX_RETRIES = env_int("CELERY_NOTIFICATION_MAX_RETRIES", 3)
CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS = env_int(
    "CELERY_NOTIFICATION_RETRY_BACKOFF_SECONDS", 30
)
CELERY_NOTIFICATION_RETRY_MAX_SECONDS = env_int(
    "CELERY_NOTIFICATION_RETRY_MAX_SECONDS", 300
)
CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS = env_int(
    "CELERY_NOTIFICATION_PROCESSING_LEASE_SECONDS", 600
)
PAYMENT_SESSION_TIMEOUT_MINUTES = env_int("PAYMENT_SESSION_TIMEOUT_MINUTES", 20)
PAYMENT_EXPIRATION_BATCH_SIZE = env_int("PAYMENT_EXPIRATION_BATCH_SIZE", 100)
CART_GUEST_TTL_HOURS = env_int("CART_GUEST_TTL_HOURS", 72)
CART_CLEANUP_BATCH_SIZE = env_int("CART_CLEANUP_BATCH_SIZE", 200)
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
PAYMENT_WEBHOOK_BYPASS_PROVIDERS = env_csv("PAYMENT_WEBHOOK_BYPASS_PROVIDERS", "")
PAYMENT_WEBHOOK_SECRETS = env_json("PAYMENT_WEBHOOK_SECRETS_JSON", {})
PAYMENT_WEBHOOK_SIGNATURE_HEADERS = env_json(
    "PAYMENT_WEBHOOK_SIGNATURE_HEADERS_JSON", {}
)
PAYMENT_PROVIDER_CONFIRMATION_URLS = env_json(
    "PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON", {}
)
PAYMENT_PROVIDER_RETURN_BASE_URL = env_required("PAYMENT_PROVIDER_RETURN_BASE_URL")
PAYMENT_PROVIDER_STATUS_OVERRIDES = env_json(
    "PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON", {}
)
DELIVERY_PROVIDER_TRACKING_OVERRIDES = env_json(
    "DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON", {}
)

_validate_secret_key(SECRET_KEY)
_validate_database_url(DATABASE_URL)
_validate_redis_url("REDIS_URL", REDIS_URL)
_validate_redis_url("CELERY_BROKER_URL", CELERY_BROKER_URL)
_validate_redis_url("CELERY_RESULT_BACKEND", CELERY_RESULT_BACKEND)
_validate_hosts("ALLOWED_HOSTS", ALLOWED_HOSTS)
_validate_http_origins("CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS)
_validate_http_origins("CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS)
_validate_smtp_settings()
_validate_s3_settings()
_validate_payment_webhook_settings()
_validate_no_sandbox_overrides()
_validate_celery_notification_settings()
_validate_background_cleanup_settings()

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
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
