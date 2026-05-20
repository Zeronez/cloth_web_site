from config.settings.base import *  # noqa: F403

DEBUG = True
USE_REDIS_CACHE = False

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "animeattire-dev",
    }
}
