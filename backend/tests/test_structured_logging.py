import json
import logging

import pytest
from django.test import override_settings

from config.celery import (
    TASK_CONTEXT_HEADER,
    _extract_task_log_context,
    inject_task_log_context,
    log_task_failure,
)
from config.logging import (
    JsonFormatter,
    bind_log_context,
    get_log_context,
    reset_log_context,
    sanitize_log_text,
    scrub_log_payload,
)


pytestmark = pytest.mark.django_db


def test_request_context_middleware_generates_request_headers(client):
    response = client.get("/api/health/live/")

    assert response.status_code == 200
    assert response["X-Request-ID"]
    assert response["X-Correlation-ID"] == response["X-Request-ID"]


def test_request_context_middleware_accepts_safe_incoming_ids(client):
    response = client.get(
        "/api/health/live/",
        HTTP_X_REQUEST_ID="req-123",
        HTTP_X_CORRELATION_ID="checkout-flow-456",
    )

    assert response["X-Request-ID"] == "req-123"
    assert response["X-Correlation-ID"] == "checkout-flow-456"


def test_request_context_middleware_rejects_unsafe_incoming_id(client):
    response = client.get(
        "/api/health/live/",
        HTTP_X_REQUEST_ID="bad id with spaces",
    )

    assert response["X-Request-ID"] != "bad id with spaces"
    assert len(response["X-Request-ID"]) == 32


@override_settings(LOGGING_CONFIG=None)
def test_request_completed_log_contains_context_without_query_pii(client):
    captured_records = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            captured_records.append(record)

    logger = logging.getLogger("animeattire.request")
    handler = CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        response = client.get(
            "/api/health/live/?email=secret@example.com",
            HTTP_X_REQUEST_ID="req-log-1",
            HTTP_X_CORRELATION_ID="corr-log-1",
        )
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    record = captured_records[0]
    assert record.request_id == "req-log-1"
    assert record.correlation_id == "corr-log-1"
    assert record.user_id == "-"
    assert record.order_id == "-"
    assert record.method == "GET"
    assert record.path == "/api/health/live/"
    assert "secret@example.com" not in record.path


def test_json_formatter_serializes_context_fields():
    record = logging.LogRecord(
        name="animeattire.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="checkout event",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-1"
    record.correlation_id = "corr-1"
    record.user_id = "42"
    record.order_id = "100"
    record.status_code = 201

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "checkout event"
    assert payload["request_id"] == "req-1"
    assert payload["correlation_id"] == "corr-1"
    assert payload["user_id"] == "42"
    assert payload["order_id"] == "100"
    assert payload["status_code"] == 201


def test_json_formatter_scrubs_payload_metadata():
    record = logging.LogRecord(
        name="animeattire.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="profile update",
        args=(),
        exc_info=None,
    )
    record.payload = {
        "email": "shopper@example.com",
        "shipping_phone": "+79991234567",
        "safe": "hoodie",
    }

    payload = json.loads(JsonFormatter().format(record))

    assert payload["payload"]["email"] == "[redacted]"
    assert payload["payload"]["shipping_phone"] == "[redacted]"
    assert payload["payload"]["safe"] == "hoodie"


def test_log_context_is_cleared_after_request(client):
    client.get("/api/health/live/", HTTP_X_REQUEST_ID="req-cleanup")

    assert get_log_context() == {
        "request_id": "-",
        "correlation_id": "-",
        "user_id": "-",
        "order_id": "-",
    }


def test_celery_publish_injects_request_and_correlation_context():
    tokens = bind_log_context(
        request_id="req-task-1",
        correlation_id="corr-task-1",
        user_id="42",
        order_id="501",
    )
    try:
        headers = {}
        inject_task_log_context(headers=headers)
    finally:
        reset_log_context(tokens)

    assert headers[TASK_CONTEXT_HEADER] == {
        "request_id": "req-task-1",
        "correlation_id": "corr-task-1",
        "user_id": "42",
        "order_id": "501",
    }


def test_extract_task_log_context_fails_closed_on_invalid_headers():
    context = _extract_task_log_context(
        {
            TASK_CONTEXT_HEADER: {
                "request_id": "bad id with spaces",
                "correlation_id": "corr.task:1",
                "user_id": 17,
                "order_id": "",
            }
        }
    )

    assert context == {
        "request_id": "-",
        "correlation_id": "corr.task:1",
        "user_id": "17",
        "order_id": "-",
    }


@override_settings(LOGGING_CONFIG=None)
def test_celery_task_failure_log_contains_correlation_id():
    captured_records = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            captured_records.append(record)

    logger = logging.getLogger("animeattire.celery")
    handler = CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    tokens = bind_log_context(
        request_id="req-celery-fail-1",
        correlation_id="corr-celery-fail-1",
        user_id="7",
        order_id="9001",
    )
    try:
        try:
            raise RuntimeError(
                "provider gateway timeout for shopper@example.com token=secret-123"
            )
        except RuntimeError as exc:
            log_task_failure(
                task_id="task-123",
                exception=exc,
                sender=type(
                    "Sender",
                    (),
                    {"name": "notifications.send_order_confirmation_email"},
                )(),
            )
    finally:
        reset_log_context(tokens)
        logger.removeHandler(handler)

    record = captured_records[0]
    assert record.request_id == "req-celery-fail-1"
    assert record.correlation_id == "corr-celery-fail-1"
    assert record.user_id == "7"
    assert record.order_id == "9001"
    assert record.task_id == "task-123"
    assert record.task_name == "notifications.send_order_confirmation_email"
    assert "provider gateway timeout" in record.getMessage()
    assert "shopper@example.com" not in record.getMessage()
    assert "secret-123" not in record.getMessage()
    assert record.exception_type == "RuntimeError"
    assert record.exc_info is None


def test_scrub_log_payload_redacts_pii_and_secrets_recursively():
    payload = {
        "username": "shopper",
        "email": "shopper@example.com",
        "phone": "+79991234567",
        "password": "GhibliMerch!2026",
        "access_token": "jwt-token",
        "shipping_line1": "Hidden street 1",
        "nested": {
            "signature": "webhook-signature",
            "safe_field": "anime hoodie",
        },
    }

    scrubbed = scrub_log_payload(payload)

    assert scrubbed["username"] == "shopper"
    assert scrubbed["email"] == "[redacted]"
    assert scrubbed["phone"] == "[redacted]"
    assert scrubbed["password"] == "[redacted]"
    assert scrubbed["access_token"] == "[redacted]"
    assert scrubbed["shipping_line1"] == "[redacted]"
    assert scrubbed["nested"]["signature"] == "[redacted]"
    assert scrubbed["nested"]["safe_field"] == "anime hoodie"

    serialized = str(scrubbed)
    assert "shopper@example.com" not in serialized
    assert "+79991234567" not in serialized
    assert "GhibliMerch!2026" not in serialized
    assert "jwt-token" not in serialized


def test_sanitize_log_text_redacts_inline_pii():
    text = sanitize_log_text(
        "customer=shopper@example.com phone=+79991234567 token=secret-123"
    )

    assert "shopper@example.com" not in text
    assert "+79991234567" not in text
    assert "secret-123" not in text
