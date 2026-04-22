from config.settings.base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "animeattire-test-secret-key-with-enough-entropy-for-hmac"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
