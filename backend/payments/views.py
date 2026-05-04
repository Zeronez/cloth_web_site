from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment, PaymentMethod
from payments.serializers import (
    PaymentMethodSerializer,
    PaymentReturnStatusQuerySerializer,
    PaymentReturnStatusSerializer,
    PaymentSerializer,
    PaymentSessionCreateSerializer,
    PaymentWebhookResponseSerializer,
    PaymentWebhookSerializer,
)
from payments.signatures import verify_payment_webhook_signature
from payments.services import (
    create_payment_session,
    get_payment_return_status,
    process_payment_webhook,
)


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
        payment, session, created = create_payment_session(
            user=request.user, **serializer.validated_data
        )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "payment": PaymentSerializer(
                    payment, context=self.get_serializer_context()
                ).data,
                "created": created,
                "provider": session.provider,
                "confirmation_url": session.confirmation_url,
                "message": session.message,
            },
            status=response_status,
        )

    @action(detail=True, methods=["get"], url_path="return-status")
    def return_status(self, request, pk=None):
        query_serializer = PaymentReturnStatusQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        result = get_payment_return_status(
            user=request.user,
            payment_id=pk,
            serializer_context=self.get_serializer_context(),
            provider_code=query_serializer.validated_data.get("provider", ""),
            external_payment_id=query_serializer.validated_data.get(
                "external_payment_id", ""
            ),
        )
        serializer = PaymentReturnStatusSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request, provider_code):
        verify_payment_webhook_signature(
            provider_code=provider_code,
            raw_body=request.body,
            headers=request.headers,
        )
        serializer = PaymentWebhookSerializer(
            data=request.data,
            context={"provider_code": provider_code},
        )
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        payload.pop("provider", None)
        result = process_payment_webhook(
            provider_code=provider_code,
            **payload,
        )
        response = PaymentWebhookResponseSerializer(result)
        return Response(response.data, status=status.HTTP_200_OK)
