from rest_framework import serializers

from catalog.serializers import ProductListSerializer
from favorites.models import FavoriteProduct


class FavoriteProductSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = FavoriteProduct
        fields = ("id", "product", "created_at")
        read_only_fields = ("id", "product", "created_at")


class FavoriteCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
