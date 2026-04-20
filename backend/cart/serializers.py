from rest_framework import serializers

from cart.models import Cart, CartItem
from catalog.serializers import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = ("id", "variant", "quantity", "line_total", "created_at", "updated_at")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = (
            "id",
            "items",
            "total_amount",
            "total_quantity",
            "created_at",
            "updated_at",
        )


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class SetCartItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)
