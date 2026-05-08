import pytest
from django.core.cache import cache
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)
from rest_framework.settings import reload_api_settings
from rest_framework.views import APIView

from catalog.models import ProductVariant


pytestmark = pytest.mark.django_db


@pytest.fixture
def throttle_api_settings(settings):
    original_rest_framework = settings.REST_FRAMEWORK
    original_api_view_throttle_classes = APIView.throttle_classes
    original_simple_throttle_rates = SimpleRateThrottle.THROTTLE_RATES
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": (
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
            "rest_framework.throttling.ScopedRateThrottle",
        ),
        "DEFAULT_THROTTLE_RATES": {
            "anon": "1000/min",
            "user": "1000/min",
            "auth": "2/min",
            "catalog": "2/min",
            "cart": "2/min",
            "checkout": "2/min",
            "payment": "2/min",
            "support": "2/min",
            "webhook": "2/min",
        },
    }
    reload_api_settings(setting="REST_FRAMEWORK", value=settings.REST_FRAMEWORK)
    APIView.throttle_classes = [
        AnonRateThrottle,
        UserRateThrottle,
        ScopedRateThrottle,
    ]
    SimpleRateThrottle.THROTTLE_RATES = settings.REST_FRAMEWORK[
        "DEFAULT_THROTTLE_RATES"
    ]
    cache.clear()
    yield
    cache.clear()
    settings.REST_FRAMEWORK = original_rest_framework
    APIView.throttle_classes = original_api_view_throttle_classes
    SimpleRateThrottle.THROTTLE_RATES = original_simple_throttle_rates
    reload_api_settings(setting="REST_FRAMEWORK", value=settings.REST_FRAMEWORK)


def assert_throttled_after_two_attempts(
    api_client, method, path, payload=None, **extra
):
    first_response = getattr(api_client, method)(path, payload or {}, **extra)
    second_response = getattr(api_client, method)(path, payload or {}, **extra)
    throttled_response = getattr(api_client, method)(path, payload or {}, **extra)

    assert first_response.status_code != 429
    assert second_response.status_code != 429
    assert throttled_response.status_code == 429
    assert throttled_response.data["error"]["code"] == "throttled"
    assert throttled_response.data["error"]["message"] == (
        "Слишком много запросов. Повторите позже."
    )
    assert throttled_response.data["error"]["details"]["detail"]["code"] == "throttled"

    return first_response, second_response, throttled_response


def test_auth_token_is_throttled_by_guest_ip(api_client, throttle_api_settings):
    payload = {"username": "missing", "password": "wrong"}

    assert_throttled_after_two_attempts(
        api_client,
        "post",
        "/api/auth/token/",
        payload,
        format="json",
        REMOTE_ADDR="198.51.100.10",
    )

    other_ip_response = api_client.post(
        "/api/auth/token/",
        payload,
        format="json",
        REMOTE_ADDR="198.51.100.11",
    )
    assert other_ip_response.status_code != 429


def test_public_catalog_is_throttled_by_guest_ip(
    api_client, product_factory, throttle_api_settings
):
    product_factory(name="Akira tech hoodie")

    assert_throttled_after_two_attempts(
        api_client,
        "get",
        "/api/products/",
        REMOTE_ADDR="203.0.113.20",
    )

    other_ip_response = api_client.get(
        "/api/products/",
        REMOTE_ADDR="203.0.113.21",
    )
    assert other_ip_response.status_code == 200


def test_cart_write_is_throttled_per_authenticated_user(
    api_client, user, other_user, product_factory, throttle_api_settings
):
    product = product_factory(name="Eva-01 tee")
    variant = ProductVariant.objects.get(product=product)
    payload = {"variant_id": variant.id, "quantity": 1}

    api_client.force_authenticate(user=user)
    assert_throttled_after_two_attempts(
        api_client,
        "post",
        "/api/cart/items/",
        payload,
        format="json",
    )

    api_client.force_authenticate(user=other_user)
    other_user_response = api_client.post(
        "/api/cart/items/",
        payload,
        format="json",
    )
    assert other_user_response.status_code == 201


@pytest.mark.parametrize(
    ("path", "payload"),
    (
        ("/api/orders/checkout/", {}),
        ("/api/payments/sessions/", {}),
    ),
)
def test_sensitive_authenticated_writes_are_throttled(
    api_client, user, path, payload, throttle_api_settings
):
    api_client.force_authenticate(user=user)

    assert_throttled_after_two_attempts(
        api_client,
        "post",
        path,
        payload,
        format="json",
    )


def test_support_contact_requests_are_throttled_by_guest_ip(
    api_client, throttle_api_settings
):
    payload = {
        "name": "Shopper",
        "email": "shopper@example.com",
        "message": "Please tell me when size L will be available.",
    }

    assert_throttled_after_two_attempts(
        api_client,
        "post",
        "/api/contact-requests/",
        payload,
        format="json",
        REMOTE_ADDR="192.0.2.30",
    )
