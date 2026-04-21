from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.models import Payment, PaymentMethod
from payments.serializers import (
    PaymentMethodSerializer,
    PaymentSerializer,
    PaymentSessionCreateSerializer,
)
from payments.services import create_payment_session


class PaymentMethodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        return PaymentMethod.objects.filter(is_active=True).order_by(
            "sort_order", "name"
        )


class PaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Payment.objects.filter(user=self.request.user)
            .select_related("order", "method")
            .prefetch_related("events")
            .order_by("-created_at")
        )

    @action(detail=False, methods=["post"], url_path="sessions")
    def create_session(self, request):
        serializer = PaymentSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment, created = create_payment_session(
            user=request.user, **serializer.validated_data
        )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "payment": PaymentSerializer(
                    payment, context=self.get_serializer_context()
                ).data,
                "created": created,
                "provider": "placeholder",
                "confirmation_url": None,
                "message": "Платежная сессия создана локально. Внешний провайдер не подключен.",
            },
            status=response_status,
        )
