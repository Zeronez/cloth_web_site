from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


@extend_schema(auth=[], responses={200: dict})
@api_view(["GET"])
def live(request):
    return Response({"status": "ok", "service": "animeattire-api"})


@extend_schema(auth=[], responses={200: dict, 503: dict})
@api_view(["GET"])
def ready(request):
    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
    }
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
