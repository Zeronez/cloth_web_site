import pytest


pytestmark = pytest.mark.django_db


REQUIRED_PATHS = {
    "/api/health/live/",
    "/api/health/ready/",
    "/api/auth/register/",
    "/api/auth/logout/",
    "/api/auth/token/",
    "/api/auth/token/refresh/",
    "/api/users/me/",
    "/api/categories/",
    "/api/franchises/",
    "/api/products/",
    "/api/cart/",
    "/api/orders/",
    "/api/orders/checkout/",
    "/api/delivery-methods/",
    "/api/payment-methods/",
    "/api/payments/",
    "/api/payments/sessions/",
    "/api/addresses/",
    "/api/favorites/",
    "/api/contact-requests/",
}


PROTECTED_PATHS = {
    "/api/users/me/",
    "/api/addresses/",
    "/api/orders/",
    "/api/orders/checkout/",
    "/api/payments/",
    "/api/payments/sessions/",
    "/api/favorites/",
}


PUBLIC_PATHS = {
    "/api/health/live/",
    "/api/health/ready/",
    "/api/products/",
    "/api/categories/",
    "/api/franchises/",
    "/api/delivery-methods/",
    "/api/payment-methods/",
    "/api/contact-requests/",
    "/api/auth/register/",
    "/api/auth/token/",
    "/api/auth/token/refresh/",
}


def get_schema(client):
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    return response.json()


def operation_security(schema, path):
    operations = schema["paths"][path]
    return [
        operation.get("security", [])
        for method, operation in operations.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]


def test_openapi_schema_endpoint_exposes_contract(client):
    schema = get_schema(client)

    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "AnimeAttire API"
    assert schema["paths"]
    assert "components" in schema
    assert "jwtAuth" in schema["components"]["securitySchemes"]
    assert REQUIRED_PATHS.issubset(set(schema["paths"]))


def test_openapi_docs_endpoints_are_public(client):
    swagger_response = client.get("/api/docs/")
    redoc_response = client.get("/api/redoc/")

    assert swagger_response.status_code == 200
    assert redoc_response.status_code == 200
    assert b"Swagger" in swagger_response.content
    assert b"redoc" in redoc_response.content.lower()


def test_openapi_marks_protected_paths_with_jwt_security(client):
    schema = get_schema(client)

    for path in PROTECTED_PATHS:
        security_entries = operation_security(schema, path)
        assert security_entries, path
        assert any(
            any("jwtAuth" in requirement for requirement in operation_security)
            for operation_security in security_entries
        ), path


def test_openapi_keeps_public_paths_anonymous_capable(client):
    schema = get_schema(client)

    for path in PUBLIC_PATHS:
        security_entries = operation_security(schema, path)
        assert security_entries, path
        assert any(
            operation_security in (None, [])
            or [] in operation_security
            or {} in operation_security
            for operation_security in security_entries
        ), path
