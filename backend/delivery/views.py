from rest_framework import mixins, viewsets

from delivery.models import DeliveryMethod
from delivery.serializers import DeliveryMethodSerializer


class DeliveryMethodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DeliveryMethodSerializer

    def get_queryset(self):
        return DeliveryMethod.objects.filter(is_active=True).order_by(
            "sort_order", "name"
        )
