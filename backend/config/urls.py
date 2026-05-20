from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from cart.views import CartViewSet
from catalog.views import AnimeFranchiseViewSet, CategoryViewSet, ProductViewSet
from config import health
from delivery.views import DeliveryMethodViewSet
from favorites.views import FavoriteProductViewSet
from orders.views import OrderViewSet
from payments.views import PaymentMethodViewSet, PaymentViewSet
from payments.views import PaymentWebhookView
from support.views import ContactRequestViewSet
from users.views import (
    AccountDeleteView,
    AccountExportView,
    AddressViewSet,
    EmailConfirmationConfirmView,
    EmailConfirmationRequestView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PhoneConfirmationConfirmView,
    PhoneConfirmationRequestView,
    RegisterView,
    ScopedTokenObtainPairView,
    ScopedTokenRefreshView,
    UserMeView,
    logout,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("franchises", AnimeFranchiseViewSet, basename="franchise")
router.register("products", ProductViewSet, basename="product")
router.register("cart", CartViewSet, basename="cart")
router.register("orders", OrderViewSet, basename="order")
router.register("delivery-methods", DeliveryMethodViewSet, basename="delivery-method")
router.register("payment-methods", PaymentMethodViewSet, basename="payment-method")
router.register("payments", PaymentViewSet, basename="payment")
router.register("addresses", AddressViewSet, basename="address")
router.register("favorites", FavoriteProductViewSet, basename="favorite")
router.register("contact-requests", ContactRequestViewSet, basename="contact-request")


def build_api_urlpatterns(*, schema_url_name):
    return [
        path("health/live/", health.live, name="health_live"),
        path("health/ready/", health.ready, name="health_ready"),
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "docs/",
            SpectacularSwaggerView.as_view(url_name=schema_url_name),
            name="swagger",
        ),
        path(
            "redoc/",
            SpectacularRedocView.as_view(url_name=schema_url_name),
            name="redoc",
        ),
        path("auth/register/", RegisterView.as_view(), name="auth_register"),
        path("auth/logout/", logout, name="auth_logout"),
        path(
            "auth/token/",
            ScopedTokenObtainPairView.as_view(),
            name="token_obtain_pair",
        ),
        path(
            "auth/token/refresh/",
            ScopedTokenRefreshView.as_view(),
            name="token_refresh",
        ),
        path("users/me/", UserMeView.as_view(), name="user_me"),
        path("users/me/export/", AccountExportView.as_view(), name="user_me_export"),
        path("users/me/delete/", AccountDeleteView.as_view(), name="user_me_delete"),
        path(
            "auth/password-reset/request/",
            PasswordResetRequestView.as_view(),
            name="password_reset_request",
        ),
        path(
            "auth/password-reset/confirm/",
            PasswordResetConfirmView.as_view(),
            name="password_reset_confirm",
        ),
        path(
            "auth/email-confirmation/request/",
            EmailConfirmationRequestView.as_view(),
            name="email_confirmation_request",
        ),
        path(
            "auth/email-confirmation/confirm/",
            EmailConfirmationConfirmView.as_view(),
            name="email_confirmation_confirm",
        ),
        path(
            "auth/phone-confirmation/request/",
            PhoneConfirmationRequestView.as_view(),
            name="phone_confirmation_request",
        ),
        path(
            "auth/phone-confirmation/confirm/",
            PhoneConfirmationConfirmView.as_view(),
            name="phone_confirmation_confirm",
        ),
        path(
            "payments/webhooks/<slug:provider_code>/",
            PaymentWebhookView.as_view(),
            name="payment_webhook",
        ),
        path("", include(router.urls)),
    ]


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/v1/",
        include(
            (
                build_api_urlpatterns(schema_url_name="api_v1:schema"),
                "api_v1",
            ),
            namespace="api_v1",
        ),
    ),
    path(
        "api/",
        include(
            (
                build_api_urlpatterns(schema_url_name="api_legacy:schema"),
                "api_legacy",
            ),
            namespace="api_legacy",
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
