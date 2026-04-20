from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import Product
from favorites.models import FavoriteProduct
from favorites.serializers import FavoriteCreateSerializer, FavoriteProductSerializer


class FavoriteProductViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            FavoriteProduct.objects.filter(user=self.request.user)
            .select_related("product", "product__category", "product__franchise")
            .prefetch_related("product__images", "product__variants")
        )

    def list(self, request):
        serializer = FavoriteProductSerializer(
            self.get_queryset(),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = get_object_or_404(
            Product.objects.filter(is_active=True),
            pk=serializer.validated_data["product_id"],
        )
        favorite, _ = FavoriteProduct.objects.get_or_create(
            user=request.user,
            product=product,
        )
        return Response(
            FavoriteProductSerializer(
                favorite,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["delete"], url_path=r"products/(?P<product_id>\d+)")
    def remove_product(self, request, product_id=None):
        FavoriteProduct.objects.filter(
            user=request.user, product_id=product_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
