from rest_framework import serializers

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    ProductTag,
    ProductVariant,
    SizeChart,
)
from catalog.services import build_size_recommendation
from catalog.tag_translations import get_tag_label


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description")


class AnimeFranchiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimeFranchise
        fields = ("id", "name", "slug", "description")


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    variant_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ("id", "url", "alt_text", "is_main", "sort_order", "variant_id")

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return ""
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "size",
            "color",
            "stock_quantity",
            "price_delta",
            "price",
            "is_active",
        )


class ProductTagSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = ProductTag
        fields = ("id", "name", "slug", "label")

    def get_label(self, obj):
        return get_tag_label(obj.slug, obj.name)


class SizeChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeChart
        fields = ("id", "title", "measurements", "notes", "category_id", "product_id")


class ProductRecommendationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "recommendation_fit_tendency",
            "recommendation_fit_confidence",
            "recommendation_silhouette",
            "recommendation_style_tags",
            "recommendation_seasonality",
            "recommendation_layering_role",
            "recommendation_body_shape_notes",
            "recommendation_notes",
        )


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    franchise = AnimeFranchiseSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    total_stock = serializers.IntegerField(read_only=True)
    tags = ProductTagSerializer(many=True, read_only=True)
    fit_recommendation = serializers.SerializerMethodField()
    recommendation_metadata = ProductRecommendationMetadataSerializer(read_only=True, source="*")

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "franchise",
            "base_price",
            "is_featured",
            "main_image",
            "total_stock",
            "tags",
            "recommendation_metadata",
            "fit_recommendation",
        )

    def get_main_image(self, obj):
        image = next((item for item in obj.images.all() if item.is_main), None)
        if image is None:
            image = next(iter(obj.images.all()), None)
        return (
            ProductImageSerializer(image, context=self.context).data if image else None
        )

    def get_fit_recommendation(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return build_size_recommendation(product=obj, user=user)


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = serializers.SerializerMethodField()
    tags = ProductTagSerializer(many=True, read_only=True)
    size_charts = SizeChartSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "description",
            "images",
            "variants",
            "tags",
            "size_charts",
            "fit_recommendation",
            "canonical_url",
            "og_image_url",
        )

    def get_variants(self, obj):
        variants = [variant for variant in obj.variants.all() if variant.is_active]
        return ProductVariantSerializer(
            variants,
            many=True,
            context=self.context,
        ).data
