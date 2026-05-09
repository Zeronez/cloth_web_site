import redis
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.celery import app as celery_app


@extend_schema(auth=[], responses={200: dict})
@api_view(["GET"])
@permission_classes([AllowAny])
def live(request):
    return Response({"status": "ok", "service": "animeattire-api"})


@extend_schema(auth=[], responses={200: dict, 503: dict})
@api_view(["GET"])
@permission_classes([AllowAny])
def ready(request):
    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
    }
    checks.update(_check_celery())
    status_code = 200 if all(checks.values()) else 503
    return Response(
        {
            "status": "ok" if status_code == 200 else "degraded",
            "checks": checks,
        },
        status=status_code,
    )


def _check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _check_redis():
    try:
        key = "health:ready"
        cache.set(key, "ok", timeout=5)
        return cache.get(key) == "ok"
    except Exception:
        return False


def _check_celery():
    if not settings.HEALTH_CHECK_CELERY_ENABLED:
        return {}

    checks = {"celery_broker": _check_redis_url(settings.CELERY_BROKER_URL)}
    if settings.HEALTH_CHECK_CELERY_RESULT_BACKEND_ENABLED:
        checks["celery_result_backend"] = _check_redis_url(
            settings.CELERY_RESULT_BACKEND
        )
    if settings.HEALTH_CHECK_CELERY_WORKERS_ENABLED:
        checks["celery_workers"] = _check_celery_workers()
    return checks


def _check_redis_url(url, timeout=None):
    try:
        timeout = timeout or settings.HEALTH_CHECK_CELERY_TIMEOUT_SECONDS
        client = redis.Redis.from_url(
            url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        return client.ping() is True
    except Exception:
        return False


def _check_celery_workers(timeout=None):
    try:
        timeout = timeout or settings.HEALTH_CHECK_CELERY_WORKER_TIMEOUT_SECONDS
        replies = celery_app.control.ping(timeout=timeout)
        return len(replies) >= settings.HEALTH_CHECK_CELERY_MIN_WORKERS
    except Exception:
        return False
