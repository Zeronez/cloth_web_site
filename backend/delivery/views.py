from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets

from delivery.models import DeliveryMethod
from delivery.serializers import DeliveryMethodSerializer


class DeliveryMethodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DeliveryMethodSerializer
    throttle_scope = "catalog"

    @extend_schema(auth=[])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return DeliveryMethod.objects.filter(is_active=True).order_by(
            "sort_order", "name"
        )
