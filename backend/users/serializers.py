from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from users.models import Address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_email_verified = serializers.BooleanField(read_only=True)
    has_accepted_privacy_policy = serializers.BooleanField(read_only=True)
    privacy_policy_version = serializers.CharField(read_only=True)
    has_accepted_offer_agreement = serializers.BooleanField(read_only=True)
    offer_agreement_version = serializers.CharField(read_only=True)
    is_marketing_subscribed = serializers.BooleanField(required=False)
    marketing_opt_in_version = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "is_email_verified",
            "has_accepted_privacy_policy",
            "privacy_policy_version",
            "has_accepted_offer_agreement",
            "offer_agreement_version",
            "is_marketing_subscribed",
            "marketing_opt_in_version",
        )
        read_only_fields = ("id", "username", "avatar")

    def update(self, instance, validated_data):
        marketing_subscribed = validated_data.pop("is_marketing_subscribed", None)
        instance = super().update(instance, validated_data)
        if marketing_subscribed is not None:
            instance.set_marketing_subscription(
                subscribed=marketing_subscribed,
                version=self.context["marketing_consent_version"],
            )
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    privacy_policy_accepted = serializers.BooleanField(write_only=True)
    offer_agreement_accepted = serializers.BooleanField(write_only=True)
    marketing_opt_in = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "privacy_policy_accepted",
            "offer_agreement_accepted",
            "marketing_opt_in",
        )
        read_only_fields = ("id",)

    def validate_privacy_policy_accepted(self, value):
        if not value:
            raise serializers.ValidationError(
                "Нужно принять политику конфиденциальности."
            )
        return value

    def validate_offer_agreement_accepted(self, value):
        if not value:
            raise serializers.ValidationError("Нужно принять оферту.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("privacy_policy_accepted")
        validated_data.pop("offer_agreement_accepted")
        marketing_opt_in = validated_data.pop("marketing_opt_in", False)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.mark_required_consents_accepted(
            privacy_version=self.context["privacy_policy_version"],
            offer_version=self.context["offer_agreement_version"],
        )
        if marketing_opt_in:
            user.set_marketing_subscription(
                subscribed=True,
                version=self.context["marketing_consent_version"],
            )
        return user


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "label",
            "recipient_name",
            "phone",
            "country",
            "city",
            "postal_code",
            "line1",
            "line2",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default"):
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        return Address.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_default"):
            Address.objects.filter(user=instance.user, is_default=True).exclude(
                pk=instance.pk
            ).update(is_default=False)
        return super().update(instance, validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )

    default_error_messages = {
        "invalid_token": "Ссылка для смены пароля недействительна или устарела."
    }

    def save(self, **kwargs):
        user = self.context["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        self.context["user"] = user
        return attrs


class EmailConfirmationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        "invalid_token": "Ссылка подтверждения email недействительна или устарела."
    }

    def save(self, **kwargs):
        user = self.context["user"]
        user.mark_email_verified()
        return user

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        self.context["user"] = user
        return attrs
