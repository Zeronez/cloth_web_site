from rest_framework import serializers

from payments.models import Payment, PaymentEvent, PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    session_mode_label = serializers.CharField(
        source="get_session_mode_display", read_only=True
    )

    class Meta:
        model = PaymentMethod
        fields = (
            "code",
            "name",
            "description",
            "provider_code",
            "session_mode",
            "session_mode_label",
            "currency",
            "sort_order",
        )


class PaymentEventSerializer(serializers.ModelSerializer):
    new_status_label = serializers.CharField(
        source="get_new_status_display", read_only=True
    )

    class Meta:
        model = PaymentEvent
        fields = (
            "id",
            "event_type",
            "previous_status",
            "new_status",
            "new_status_label",
            "message",
            "payload",
            "external_event_id",
            "created_at",
        )


class PaymentSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    events = PaymentEventSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "method_code",
            "provider_code",
            "status",
            "status_label",
            "amount",
            "currency",
            "external_payment_id",
            "session_expires_at",
            "events",
            "created_at",
            "updated_at",
        )


class PaymentSessionCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    payment_method_code = serializers.SlugField(max_length=48)
    idempotency_key = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )


class PaymentSessionSerializer(serializers.Serializer):
    payment = PaymentSerializer()
    created = serializers.BooleanField()
    provider = serializers.CharField()
    confirmation_url = serializers.URLField(allow_null=True)
    message = serializers.CharField()


class PaymentWebhookSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=120)
    provider = serializers.SlugField(max_length=48, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Payment.Status.choices)
    order_id = serializers.IntegerField(min_value=1)
    payment_id = serializers.IntegerField(min_value=1, required=False)
    external_payment_id = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )
    payload = serializers.JSONField(required=False)

    def validate(self, attrs):
        provider_from_path = self.context.get("provider_code", "")
        payload_provider = attrs.get("provider", "")
        if (
            payload_provider
            and provider_from_path
            and payload_provider != provider_from_path
        ):
            raise serializers.ValidationError(
                {
                    "provider": (
                        "Payload provider must match the webhook endpoint provider."
                    )
                }
            )
        attrs["provider"] = payload_provider or provider_from_path
        attrs["payload"] = attrs.get("payload") or {}
        return attrs


class PaymentWebhookResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer()
    event_id = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()
    processed = serializers.BooleanField()
    replayed = serializers.BooleanField()
    conflict = serializers.BooleanField()
