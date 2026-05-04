from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from delivery.services import refresh_order_tracking_from_provider
from orders.models import Order
from orders.serializers import CheckoutSerializer, OrderSerializer
from orders.services import checkout_cart


class OrderViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("delivery_snapshot")
            .prefetch_related("items__variant", "delivery_snapshot__tracking_events")
            .order_by("-created_at")
        )

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = checkout_cart(request.user, serializer.validated_data)
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="tracking-refresh")
    def tracking_refresh(self, request, pk=None):
        order = self.get_object()
        refresh_order_tracking_from_provider(order=order)
        order.refresh_from_db()
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )
