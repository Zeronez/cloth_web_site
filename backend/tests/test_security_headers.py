import pytest
from django.test import override_settings


pytestmark = pytest.mark.django_db


@override_settings(
    SECURE_HSTS_SECONDS=60 * 60 * 24 * 30,
    SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
    SECURE_CONTENT_TYPE_NOSNIFF=True,
    SECURE_REFERRER_POLICY="same-origin",
    X_FRAME_OPTIONS="DENY",
    CONTENT_SECURITY_POLICY="default-src 'self'; object-src 'none'; frame-ancestors 'none'",
    CONTENT_SECURITY_POLICY_REPORT_ONLY=False,
)
def test_api_response_includes_security_headers(client):
    response = client.get("/api/v1/products/", secure=True)

    assert response.status_code == 200
    assert response["Strict-Transport-Security"] == "max-age=2592000; includeSubDomains"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert response["X-Frame-Options"] == "DENY"
    assert (
        response["Content-Security-Policy"]
        == "default-src 'self'; object-src 'none'; frame-ancestors 'none'"
    )


@override_settings(
    CONTENT_SECURITY_POLICY="default-src 'self'",
    CONTENT_SECURITY_POLICY_REPORT_ONLY=True,
)
def test_report_only_policy_uses_report_only_header(client):
    response = client.get("/admin/login/")

    assert response.status_code == 200
    assert response["Content-Security-Policy-Report-Only"] == "default-src 'self'"
    assert "Content-Security-Policy" not in response
