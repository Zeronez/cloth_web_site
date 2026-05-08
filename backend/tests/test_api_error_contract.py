import pytest


pytestmark = pytest.mark.django_db


def assert_error_shape(response, *, status_code, code, message=None):
    assert response.status_code == status_code
    assert set(response.data) == {"error"}
    error = response.data["error"]
    assert error["status"] == status_code
    assert error["code"] == code
    if message is not None:
        assert error["message"] == message
    assert isinstance(error["details"], dict)
    assert error["request_id"]
    assert error["correlation_id"]
    return error


def test_validation_errors_return_stable_ru_envelope(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {"username": ""},
        format="json",
        HTTP_X_REQUEST_ID="valid-request-id-1",
    )

    error = assert_error_shape(
        response,
        status_code=400,
        code="validation_error",
        message="Проверьте введенные данные.",
    )
    assert error["request_id"] == "valid-request-id-1"
    assert error["details"]["username"][0]["code"] == "blank"
    assert error["details"]["password"][0]["code"] == "required"


def test_not_authenticated_returns_ru_envelope(api_client):
    response = api_client.get("/api/users/me/")

    error = assert_error_shape(
        response,
        status_code=401,
        code="not_authenticated",
        message="Необходима авторизация.",
    )
    assert error["details"]["detail"]["code"] == "not_authenticated"


def test_not_found_returns_ru_envelope(api_client):
    response = api_client.get("/api/products/missing-product/")

    error = assert_error_shape(
        response,
        status_code=404,
        code="not_found",
        message="Ресурс не найден.",
    )
    assert error["details"]["detail"]["code"] == "not_found"


def test_method_not_allowed_returns_ru_envelope(api_client):
    response = api_client.delete("/api/products/")

    error = assert_error_shape(
        response,
        status_code=405,
        code="method_not_allowed",
        message="Метод запроса не поддерживается.",
    )
    assert error["details"]["detail"]["code"] == "method_not_allowed"


def test_parse_error_returns_ru_envelope(api_client):
    response = api_client.generic(
        "POST",
        "/api/auth/register/",
        data="{",
        content_type="application/json",
    )

    error = assert_error_shape(
        response,
        status_code=400,
        code="parse_error",
        message="Проверьте введенные данные.",
    )
    assert error["details"]["detail"]["code"] == "parse_error"


def test_unsupported_media_type_returns_ru_envelope(authenticated_client):
    response = authenticated_client.post(
        "/api/cart/items/",
        data="variant_id=1&quantity=1",
        content_type="text/plain",
    )

    error = assert_error_shape(
        response,
        status_code=415,
        code="unsupported_media_type",
        message="Формат запроса не поддерживается.",
    )
    assert error["details"]["detail"]["code"] == "unsupported_media_type"


def test_business_validation_error_promotes_domain_code(
    authenticated_client, product_factory
):
    product = product_factory(name="Low Stock Tee", variants=[{"stock_quantity": 1}])
    variant = product.variants.get()
    authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    response = authenticated_client.post(
        "/api/cart/items/",
        {"variant_id": variant.id, "quantity": 1},
        format="json",
    )

    error = assert_error_shape(
        response,
        status_code=400,
        code="validation_error",
        message="Проверьте введенные данные.",
    )
    assert error["details"]["quantity"][0]["code"] == "invalid"
