from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from catalog.filters import ProductFilter
from catalog.models import AnimeFranchise, Category, Product, ProductImage
from catalog.serializers import (
    AnimeFranchiseSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


@extend_schema_view(list=extend_schema(auth=[]), retrieve=extend_schema(auth=[]))
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    search_fields = ("name",)
    throttle_scope = "catalog"


@extend_schema_view(list=extend_schema(auth=[]), retrieve=extend_schema(auth=[]))
class AnimeFranchiseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnimeFranchise.objects.filter(is_active=True)
    permission_classes = (AllowAny,)
    serializer_class = AnimeFranchiseSerializer
    lookup_field = "slug"
    search_fields = ("name",)
    throttle_scope = "catalog"


@extend_schema_view(list=extend_schema(auth=[]), retrieve=extend_schema(auth=[]))
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects.filter(status=Product.PublishingStatus.ACTIVE)
        .select_related("category", "franchise")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.filter(is_approved=True)),
            "variants",
            "videos",
            "tags",
            "collections",
        )
    )
    filterset_class = ProductFilter
    permission_classes = (AllowAny,)
    search_fields = (
        "name",
        "description",
        "search_synonyms",
        "material",
        "fit",
        "franchise__name",
        "category__name",
        "tags__name",
    )
    ordering_fields = ("base_price", "created_at", "name")
    ordering = ("-is_featured", "-created_at")
    lookup_field = "slug"
    throttle_scope = "catalog"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
