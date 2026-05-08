import pytest

from config import health


pytestmark = pytest.mark.django_db


def test_liveness_endpoint_is_public(client):
    response = client.get("/api/health/live/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "animeattire-api"}


def test_readiness_endpoint_reports_database_redis_and_celery(client, monkeypatch):
    monkeypatch.setattr(health, "_check_database", lambda: True)
    monkeypatch.setattr(health, "_check_redis", lambda: True)
    monkeypatch.setattr(
        health,
        "_check_celery",
        lambda: {"celery_broker": True, "celery_result_backend": True},
    )

    response = client.get("/api/health/ready/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": True,
            "redis": True,
            "celery_broker": True,
            "celery_result_backend": True,
        },
    }


def test_readiness_endpoint_degrades_when_celery_broker_is_unavailable(
    client, monkeypatch
):
    monkeypatch.setattr(health, "_check_database", lambda: True)
    monkeypatch.setattr(health, "_check_redis", lambda: True)
    monkeypatch.setattr(
        health,
        "_check_celery",
        lambda: {"celery_broker": False, "celery_result_backend": True},
    )

    response = client.get("/api/health/ready/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "database": True,
            "redis": True,
            "celery_broker": False,
            "celery_result_backend": True,
        },
    }


def test_celery_check_returns_broker_and_result_backend_status(settings, monkeypatch):
    settings.HEALTH_CHECK_CELERY_ENABLED = True
    settings.HEALTH_CHECK_CELERY_RESULT_BACKEND_ENABLED = True
    settings.HEALTH_CHECK_CELERY_WORKERS_ENABLED = False
    monkeypatch.setattr(
        health,
        "_check_redis_url",
        lambda url: url == settings.CELERY_BROKER_URL,
    )

    assert health._check_celery() == {
        "celery_broker": True,
        "celery_result_backend": False,
    }


def test_celery_check_can_include_opt_in_worker_status(settings, monkeypatch):
    settings.HEALTH_CHECK_CELERY_ENABLED = True
    settings.HEALTH_CHECK_CELERY_RESULT_BACKEND_ENABLED = False
    settings.HEALTH_CHECK_CELERY_WORKERS_ENABLED = True
    monkeypatch.setattr(health, "_check_redis_url", lambda url: True)
    monkeypatch.setattr(health, "_check_celery_workers", lambda: True)

    assert health._check_celery() == {
        "celery_broker": True,
        "celery_workers": True,
    }


def test_celery_check_can_be_disabled(settings):
    settings.HEALTH_CHECK_CELERY_ENABLED = False

    assert health._check_celery() == {}


def test_celery_worker_check_passes_when_worker_replies(monkeypatch):
    monkeypatch.setattr(
        health.celery_app.control,
        "ping",
        lambda timeout: [{"celery@worker": {"ok": "pong"}}],
    )

    assert health._check_celery_workers(timeout=1) is True


def test_celery_worker_check_fails_when_no_worker_replies(monkeypatch):
    monkeypatch.setattr(health.celery_app.control, "ping", lambda timeout: [])

    assert health._check_celery_workers(timeout=1) is False


def test_celery_worker_check_fails_closed_on_broker_errors(monkeypatch):
    def raise_broker_error(timeout):
        raise ConnectionError("broker unavailable")

    monkeypatch.setattr(health.celery_app.control, "ping", raise_broker_error)

    assert health._check_celery_workers(timeout=1) is False
