import json
import logging

import pytest
from django.test import override_settings

from config.logging import JsonFormatter, get_log_context, scrub_log_payload


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


def test_log_context_is_cleared_after_request(client):
    client.get("/api/health/live/", HTTP_X_REQUEST_ID="req-cleanup")

    assert get_log_context() == {
        "request_id": "-",
        "correlation_id": "-",
        "user_id": "-",
        "order_id": "-",
    }


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
