from rest_framework import serializers

from delivery.serializers import OrderDeliverySnapshotSerializer
from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(read_only=True)
    variant_id = serializers.IntegerField(read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "variant",
            "variant_id",
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
    items_count = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()
    delivery = OrderDeliverySnapshotSerializer(
        source="delivery_snapshot", read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "total_amount",
            "track_number",
            "items_count",
            "shipping_address",
            "delivery",
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

    def get_items_count(self, obj):
        prefetched_items = getattr(obj, "_prefetched_objects_cache", {}).get("items")
        if prefetched_items is not None:
            return sum(item.quantity for item in prefetched_items)
        return obj.items.count()

    def get_shipping_address(self, obj):
        return {
            "name": obj.shipping_name,
            "phone": obj.shipping_phone,
            "country": obj.shipping_country,
            "city": obj.shipping_city,
            "postal_code": obj.shipping_postal_code,
            "line1": obj.shipping_line1,
            "line2": obj.shipping_line2,
        }


class CheckoutSerializer(serializers.Serializer):
    delivery_method_code = serializers.SlugField(
        max_length=48, required=False, allow_blank=True
    )
    shipping_name = serializers.CharField(max_length=160)
    shipping_phone = serializers.CharField(max_length=32)
    shipping_country = serializers.CharField(max_length=80)
    shipping_city = serializers.CharField(max_length=120)
    shipping_postal_code = serializers.CharField(max_length=32)
    shipping_line1 = serializers.CharField(max_length=255)
    shipping_line2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
