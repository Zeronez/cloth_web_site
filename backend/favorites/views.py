from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import Product
from favorites.models import FavoriteProduct
from favorites.serializers import FavoriteCreateSerializer, FavoriteProductSerializer


class FavoriteProductViewSet(
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = FavoriteProductSerializer

    def get_queryset(self):
        return (
            FavoriteProduct.objects.filter(user=self.request.user)
            .select_related("product", "product__category", "product__franchise")
            .prefetch_related("product__images", "product__variants")
        )

    def list(self, request):
        serializer = self.get_serializer(
            self.get_queryset(),
            many=True,
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = get_object_or_404(
            Product.objects.filter(is_active=True),
            pk=serializer.validated_data["product_id"],
        )
        try:
            with transaction.atomic():
                favorite, created = FavoriteProduct.objects.get_or_create(
                    user=request.user,
                    product=product,
                )
        except IntegrityError:
            favorite = FavoriteProduct.objects.get(user=request.user, product=product)
            created = False

        response_data = self.get_serializer(favorite).data
        response_data["created"] = created
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_data, status=response_status)

    @action(detail=False, methods=["delete"], url_path=r"products/(?P<product_id>\d+)")
    def remove_product(self, request, product_id=None):
        deleted_count, _ = FavoriteProduct.objects.filter(
            user=request.user, product_id=product_id
        ).delete()
        return Response(
            {"product_id": int(product_id), "deleted": deleted_count > 0},
            status=status.HTTP_200_OK,
        )
