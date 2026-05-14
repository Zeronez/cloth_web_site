from datetime import timedelta
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers, default_methods

from config.settings.env import env_bool, env_csv, env_int, env_json, env_value

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = env_value("SECRET_KEY", "unsafe-local-secret-key")
DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_csv("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")
CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_METHODS = default_methods
CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-request-id",
    "x-correlation-id",
    "x-payment-signature",
)
CORS_EXPOSE_HEADERS = ("X-Request-ID", "X-Correlation-ID")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "users",
    "catalog",
    "cart",
    "orders",
    "delivery",
    "payments",
    "favorites",
    "notifications",
    "support",
    "audit",
]

MIDDLEWARE = [
    "config.logging.RequestContextMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

LOG_LEVEL = env_value("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "config.logging.RequestContextFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "config.logging.JsonFormatter",
        },
        "console": {
            "format": (
                "%(levelname)s %(name)s %(message)s "
                "request_id=%(request_id)s correlation_id=%(correlation_id)s "
                "user_id=%(user_id)s order_id=%(order_id)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "animeattire": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "EXCEPTION_HANDLER": "config.api_errors.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env_value("DRF_THROTTLE_ANON_RATE", "1000/min"),
        "user": env_value("DRF_THROTTLE_USER_RATE", "5000/min"),
        "auth": env_value("DRF_THROTTLE_AUTH_RATE", "60/min"),
        "catalog": env_value("DRF_THROTTLE_CATALOG_RATE", "600/min"),
        "cart": env_value("DRF_THROTTLE_CART_RATE", "300/min"),
        "checkout": env_value("DRF_THROTTLE_CHECKOUT_RATE", "60/min"),
        "payment": env_value("DRF_THROTTLE_PAYMENT_RATE", "300/min"),
        "support": env_value("DRF_THROTTLE_SUPPORT_RATE", "30/min"),
        "webhook": env_value("DRF_THROTTLE_WEBHOOK_RATE", "1200/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AnimeAttire API",
    "DESCRIPTION": "Production API contract for the Russian-first AnimeAttire anime streetwear store.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}

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

REDIS_URL = env_value("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = env_value("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env_value("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CELERY_TASK_DEFAULT_QUEUE = env_value("CELERY_TASK_DEFAULT_QUEUE", "default")
CELERY_NOTIFICATION_QUEUE = env_value("CELERY_NOTIFICATION_QUEUE", "notifications")
CELERY_TASK_ROUTES = {
    "notifications.send_order_confirmation_email": {
        "queue": CELERY_NOTIFICATION_QUEUE,
    }
}
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_ACKS_ON_FAILURE_OR_TIMEOUT = False
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
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
HEALTH_CHECK_CELERY_ENABLED = env_bool("HEALTH_CHECK_CELERY_ENABLED", True)
HEALTH_CHECK_CELERY_TIMEOUT_SECONDS = env_int("HEALTH_CHECK_CELERY_TIMEOUT_SECONDS", 1)
HEALTH_CHECK_CELERY_RESULT_BACKEND_ENABLED = env_bool(
    "HEALTH_CHECK_CELERY_RESULT_BACKEND_ENABLED", True
)
HEALTH_CHECK_CELERY_WORKERS_ENABLED = env_bool(
    "HEALTH_CHECK_CELERY_WORKERS_ENABLED", False
)
HEALTH_CHECK_CELERY_WORKER_TIMEOUT_SECONDS = env_int(
    "HEALTH_CHECK_CELERY_WORKER_TIMEOUT_SECONDS", 1
)
HEALTH_CHECK_CELERY_MIN_WORKERS = env_int("HEALTH_CHECK_CELERY_MIN_WORKERS", 1)

EMAIL_BACKEND = env_value(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env_value(
    "DEFAULT_FROM_EMAIL", "AnimeAttire <no-reply@example.com>"
)
SERVER_EMAIL = env_value("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_HOST = env_value("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_value("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_value("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
FRONTEND_APP_URL = env_value("FRONTEND_APP_URL", "http://localhost:3000")
AUTH_EMAIL_CONFIRMATION_PATH = env_value(
    "AUTH_EMAIL_CONFIRMATION_PATH", "/auth/confirm-email"
)
AUTH_PASSWORD_RESET_PATH = env_value("AUTH_PASSWORD_RESET_PATH", "/auth/reset-password")

AWS_STORAGE_BUCKET_NAME = env_value("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = env_value("AWS_S3_ENDPOINT_URL", "")
AWS_ACCESS_KEY_ID = env_value("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = env_value("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_REGION_NAME = env_value("AWS_S3_REGION_NAME", "us-east-1")

PAYMENT_WEBHOOK_BYPASS_PROVIDERS = env_csv(
    "PAYMENT_WEBHOOK_BYPASS_PROVIDERS", "manual,placeholder,local"
)
PAYMENT_WEBHOOK_SECRETS = env_json("PAYMENT_WEBHOOK_SECRETS_JSON", {})
PAYMENT_WEBHOOK_SIGNATURE_HEADERS = env_json(
    "PAYMENT_WEBHOOK_SIGNATURE_HEADERS_JSON", {}
)
PAYMENT_PROVIDER_CONFIRMATION_URLS = env_json(
    "PAYMENT_PROVIDER_CONFIRMATION_URLS_JSON",
    {"yookassa": "https://yookassa.example/checkout"},
)
PAYMENT_PROVIDER_RETURN_BASE_URL = env_value(
    "PAYMENT_PROVIDER_RETURN_BASE_URL",
    "http://localhost:3000/checkout/return",
)
PAYMENT_PROVIDER_STATUS_OVERRIDES = env_json(
    "PAYMENT_PROVIDER_STATUS_OVERRIDES_JSON",
    {},
)
DELIVERY_METHOD_AVAILABILITY_OVERRIDES = env_json(
    "DELIVERY_METHOD_AVAILABILITY_OVERRIDES_JSON",
    {},
)
DELIVERY_PROVIDER_TRACKING_OVERRIDES = env_json(
    "DELIVERY_PROVIDER_TRACKING_OVERRIDES_JSON",
    {},
)
DELIVERY_PICKUP_POINT_OVERRIDES = env_json(
    "DELIVERY_PICKUP_POINT_OVERRIDES_JSON",
    {},
)

if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
