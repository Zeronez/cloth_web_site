from config.settings.base import *  # noqa: F403

from config.settings.env import env_csv

DEBUG = True
USE_REDIS_CACHE = False

# Allow running frontend on either localhost or 127.0.0.1 without CORS/CSRF issues.
CSRF_TRUSTED_ORIGINS = env_csv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CORS_ALLOWED_ORIGINS = env_csv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "animeattire-dev",
    }
}
