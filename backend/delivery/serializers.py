from rest_framework import serializers

from delivery.models import DeliveryMethod, OrderDeliverySnapshot


class DeliveryMethodSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = DeliveryMethod
        fields = (
            "code",
            "name",
            "kind",
            "kind_label",
            "description",
            "price_amount",
            "currency",
            "estimated_days_min",
            "estimated_days_max",
            "requires_address",
            "sort_order",
        )


class OrderDeliverySnapshotSerializer(serializers.ModelSerializer):
    method_kind_label = serializers.CharField(
        source="get_method_kind_display", read_only=True
    )

    class Meta:
        model = OrderDeliverySnapshot
        fields = (
            "method_code",
            "method_name",
            "method_kind",
            "method_kind_label",
            "price_amount",
            "currency",
            "estimated_days_min",
            "estimated_days_max",
            "recipient_name",
            "recipient_phone",
            "country",
            "city",
            "postal_code",
            "line1",
            "line2",
        )
