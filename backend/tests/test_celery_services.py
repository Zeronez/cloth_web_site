import os
import uuid

import pytest
import redis
from celery.contrib.testing.worker import start_worker

from config.celery import app as celery_app


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_CELERY_SERVICE_SMOKE") != "true",
    reason="Celery/Redis service smoke test is opt-in for CI service checks.",
)


def _assert_redis_available(url):
    client = redis.Redis.from_url(url, socket_connect_timeout=3, socket_timeout=3)
    assert client.ping() is True


def test_celery_worker_round_trip_uses_redis_broker_and_backend(settings, tmp_path):
    celery_app.set_current()
    celery_app.set_default()

    from celery.contrib.testing.tasks import ping

    celery_app.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        task_always_eager=False,
        task_store_eager_result=False,
        worker_hijack_root_logger=False,
    )

    _assert_redis_available(settings.CELERY_BROKER_URL)
    _assert_redis_available(settings.CELERY_RESULT_BACKEND)

    backend_key = f"celery-smoke:{uuid.uuid4()}"
    celery_app.backend.set(backend_key, b"ok")
    try:
        assert celery_app.backend.get(backend_key) == b"ok"
    finally:
        celery_app.backend.delete(backend_key)

    worker_log = tmp_path / "celery-worker.log"
    try:
        with start_worker(
            celery_app,
            concurrency=1,
            pool="solo",
            loglevel="INFO",
            logfile=str(worker_log),
            perform_ping_check=True,
            ping_task_timeout=10,
            shutdown_timeout=10,
        ):
            result = ping.apply_async()
            assert result.get(timeout=10) == "pong"
    except Exception as exc:
        worker_output = ""
        if worker_log.exists():
            worker_output = worker_log.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Celery worker smoke check failed: {exc}\n{worker_output}")
