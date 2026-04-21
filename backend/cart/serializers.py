from rest_framework import serializers

from cart.models import Cart, CartItem
from catalog.serializers import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    product = serializers.SerializerMethodField()
    unit_price = serializers.DecimalField(
        source="variant.price", max_digits=12, decimal_places=2, read_only=True
    )
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant",
            "product",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        )

    def get_product(self, obj):
        product = obj.variant.product
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "base_price": str(product.base_price),
            "is_active": product.is_active,
        }


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    subtotal_amount = serializers.DecimalField(
        source="total_amount", max_digits=12, decimal_places=2, read_only=True
    )
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = (
            "id",
            "items",
            "total_amount",
            "subtotal_amount",
            "total_quantity",
            "created_at",
            "updated_at",
        )


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class SetCartItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)
