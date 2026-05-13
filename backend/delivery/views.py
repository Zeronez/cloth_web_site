from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from delivery.serializers import DeliveryMethodSerializer
from delivery.services import get_available_delivery_methods


class DeliveryMethodViewSet(viewsets.GenericViewSet):
    serializer_class = DeliveryMethodSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "catalog"

    @extend_schema(auth=[])
    def list(self, request, *args, **kwargs):
        methods = get_available_delivery_methods(
            country=request.query_params.get("country", ""),
            city=request.query_params.get("city", ""),
            postal_code=request.query_params.get("postal_code", ""),
        )
        page = self.paginate_queryset(methods)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(methods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
