from rest_framework import serializers

from support.models import ContactRequest


class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "topic",
            "order_number",
            "message",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at")

    def validate_message(self, value):
        normalized = value.strip()
        if len(normalized) < 20:
            raise serializers.ValidationError(
                "Опишите вопрос подробнее: минимум 20 символов."
            )
        return normalized

    def validate_name(self, value):
        return value.strip()

    def validate_phone(self, value):
        return value.strip()

    def validate_order_number(self, value):
        return value.strip()
