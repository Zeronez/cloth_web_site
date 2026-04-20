from rest_framework import viewsets

from catalog.filters import ProductFilter
from catalog.models import AnimeFranchise, Category, Product
from catalog.serializers import (
    AnimeFranchiseSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    search_fields = ("name",)


class AnimeFranchiseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnimeFranchise.objects.filter(is_active=True)
    serializer_class = AnimeFranchiseSerializer
    lookup_field = "slug"
    search_fields = ("name",)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category", "franchise")
        .prefetch_related("images", "variants")
    )
    filterset_class = ProductFilter
    search_fields = ("name", "description", "franchise__name", "category__name")
    ordering_fields = ("base_price", "created_at", "name")
    ordering = ("-is_featured", "-created_at")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
