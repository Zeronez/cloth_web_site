from rest_framework import serializers

from delivery.models import DeliveryMethod, DeliveryTrackingEvent, OrderDeliverySnapshot


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


class DeliveryTrackingEventSerializer(serializers.ModelSerializer):
    new_status_label = serializers.CharField(
        source="get_new_status_display", read_only=True
    )

    class Meta:
        model = DeliveryTrackingEvent
        fields = (
            "id",
            "event_type",
            "previous_status",
            "new_status",
            "new_status_label",
            "message",
            "location",
            "payload",
            "external_event_id",
            "happened_at",
            "created_at",
        )


class OrderDeliverySnapshotSerializer(serializers.ModelSerializer):
    method_kind_label = serializers.CharField(
        source="get_method_kind_display", read_only=True
    )
    tracking_status_label = serializers.CharField(
        source="get_tracking_status_display", read_only=True
    )
    tracking_events = DeliveryTrackingEventSerializer(many=True, read_only=True)

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
            "provider_code",
            "tracking_status",
            "tracking_status_label",
            "external_shipment_id",
            "current_location",
            "last_tracking_sync_at",
            "recipient_name",
            "recipient_phone",
            "country",
            "city",
            "postal_code",
            "line1",
            "line2",
            "tracking_events",
        )
