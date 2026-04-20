from rest_framework import serializers

from catalog.models import (
    AnimeFranchise,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


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

    class Meta:
        model = ProductImage
        fields = ("id", "url", "alt_text", "is_main", "sort_order")

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


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    franchise = AnimeFranchiseSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    total_stock = serializers.IntegerField(read_only=True)

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
        )

    def get_main_image(self, obj):
        image = next((item for item in obj.images.all() if item.is_main), None)
        if image is None:
            image = next(iter(obj.images.all()), None)
        return (
            ProductImageSerializer(image, context=self.context).data if image else None
        )


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "description",
            "images",
            "variants",
        )
