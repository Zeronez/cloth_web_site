from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok", "service": "animeattire-api"})


def ready(request):
    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
    }
    status_code = 200 if all(checks.values()) else 503
    return JsonResponse(
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
