import pytest


pytestmark = pytest.mark.django_db


def test_allowed_frontend_origin_receives_cors_headers(client):
    response = client.options(
        "/api/v1/products/",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert response.status_code == 200
    assert response["access-control-allow-origin"] == "http://localhost:3000"
    assert "GET" in response["access-control-allow-methods"]
    assert "authorization" in response["access-control-allow-headers"]
    assert "x-request-id" in response["access-control-allow-headers"]
    assert response["access-control-expose-headers"] == (
        "X-Request-ID, X-Correlation-ID"
    )
    assert "access-control-allow-credentials" not in response


def test_allowed_frontend_origin_receives_no_cookie_cors_on_actual_api_response(client):
    response = client.get(
        "/api/v1/products/",
        HTTP_ORIGIN="http://localhost:3000",
    )

    assert response.status_code == 200
    assert response["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in response


def test_disallowed_origin_does_not_receive_cors_headers(client):
    response = client.options(
        "/api/v1/products/",
        HTTP_ORIGIN="https://evil.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response


def test_cors_policy_is_limited_to_api_paths(client):
    response = client.options(
        "/admin/",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert "access-control-allow-origin" not in response
