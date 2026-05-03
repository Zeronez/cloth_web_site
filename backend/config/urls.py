from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from cart.views import CartViewSet
from catalog.views import AnimeFranchiseViewSet, CategoryViewSet, ProductViewSet
from config import health
from delivery.views import DeliveryMethodViewSet
from favorites.views import FavoriteProductViewSet
from orders.views import OrderViewSet
from payments.views import PaymentMethodViewSet, PaymentViewSet
from payments.views import PaymentWebhookView
from support.views import ContactRequestViewSet
from users.views import AddressViewSet, RegisterView, UserMeView, logout

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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/live/", health.live, name="health_live"),
    path("api/health/ready/", health.ready, name="health_ready"),
    path("api/auth/register/", RegisterView.as_view(), name="auth_register"),
    path("api/auth/logout/", logout, name="auth_logout"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/users/me/", UserMeView.as_view(), name="user_me"),
    path(
        "api/payments/webhooks/<slug:provider_code>/",
        PaymentWebhookView.as_view(),
        name="payment_webhook",
    ),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
