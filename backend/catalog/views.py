from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Prefetch
from rest_framework.filters import SearchFilter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from catalog.filters import ProductFilter
from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    RecommendationDecisionLog,
)
from catalog.services import build_size_recommendation
from catalog.serializers import (
    AnimeFranchiseSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)
from catalog.tag_translations import get_matching_tag_slugs
from users.serializers import FitProfileSerializer


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
            "size_charts",
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
        "tags__slug",
    )
    ordering_fields = ("base_price", "created_at", "name", "id")
    ordering = ("-is_featured", "-created_at", "-id")
    lookup_field = "slug"
    throttle_scope = "catalog"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def filter_queryset(self, queryset):
        for backend_class in self.filter_backends:
            if backend_class is SearchFilter:
                continue
            queryset = backend_class().filter_queryset(self.request, queryset, self)

        search_query = (self.request.query_params.get("search") or "").strip()
        if not search_query:
            return queryset.distinct()

        translated_tag_slugs = get_matching_tag_slugs(search_query)
        search_filter = (
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(search_synonyms__icontains=search_query)
            | Q(material__icontains=search_query)
            | Q(fit__icontains=search_query)
            | Q(franchise__name__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(tags__name__icontains=search_query)
            | Q(tags__slug__icontains=search_query)
        )
        if translated_tag_slugs:
            search_filter |= Q(tags__slug__in=translated_tag_slugs)

        return queryset.filter(search_filter).distinct()

    @action(detail=True, methods=["get"], permission_classes=(AllowAny,))
    def recommendation(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = FitProfileSerializer(
            data={
                key: value
                for key, value in request.query_params.items()
                if key in FitProfileSerializer().fields
            }
        )
        serializer.is_valid(raise_exception=True)
        recommendation = build_size_recommendation(
            product=product,
            user=request.user,
            profile_override=serializer.validated_data or None,
        )
        RecommendationDecisionLog.objects.create(
            product=product,
            user=request.user if getattr(request.user, "is_authenticated", False) else None,
            source=RecommendationDecisionLog.Source.RECOMMENDATION_API,
            recommended_size=recommendation.get("recommended_size") or "",
            confidence=recommendation.get("confidence") or "",
            risk_level=recommendation.get("risk_level") or "",
            warnings=recommendation.get("warnings") or [],
            reasons=recommendation.get("reasons") or [],
            fallback_action=recommendation.get("fallback_action") or "",
            profile_snapshot=serializer.data or getattr(request.user, "fit_profile", {}) or {},
        )
        return Response(recommendation)
