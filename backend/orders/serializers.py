from rest_framework import serializers

from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "variant",
            "product_name",
            "sku",
            "size",
            "color",
            "quantity",
            "price_at_purchase",
            "line_total",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "total_amount",
            "track_number",
            "shipping_name",
            "shipping_phone",
            "shipping_country",
            "shipping_city",
            "shipping_postal_code",
            "shipping_line1",
            "shipping_line2",
            "items",
            "created_at",
            "updated_at",
        )


class CheckoutSerializer(serializers.Serializer):
    shipping_name = serializers.CharField(max_length=160)
    shipping_phone = serializers.CharField(max_length=32)
    shipping_country = serializers.CharField(max_length=80)
    shipping_city = serializers.CharField(max_length=120)
    shipping_postal_code = serializers.CharField(max_length=32)
    shipping_line1 = serializers.CharField(max_length=255)
    shipping_line2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
