from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import Address, PhoneConfirmation
from users.security import (
    clear_login_failures,
    clear_password_reset_confirm_failures,
    ensure_login_allowed,
    ensure_password_reset_confirm_allowed,
    record_login_failure,
    record_password_reset_confirm_failure,
)

User = get_user_model()


class BruteForceAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        request = self.context["request"]
        username = attrs.get(self.username_field, "")

        ensure_login_allowed(request, username)
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            record_login_failure(request, username)
            raise

        clear_login_failures(request, username)
        return data


class UserSerializer(serializers.ModelSerializer):
    is_email_verified = serializers.BooleanField(read_only=True)
    is_phone_verified = serializers.BooleanField(read_only=True)
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
            "is_phone_verified",
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


class DeleteAccountSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_password": "Current password is invalid.",
    }

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(self.error_messages["invalid_password"])
        return value


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
        request = self.context["request"]
        ensure_password_reset_confirm_allowed(request, attrs["uid"])

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            record_password_reset_confirm_failure(request, attrs["uid"])
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        if not default_token_generator.check_token(user, attrs["token"]):
            record_password_reset_confirm_failure(request, attrs["uid"])
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]}
            )

        clear_password_reset_confirm_failures(request, attrs["uid"])
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


class PhoneConfirmationRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)

    default_error_messages = {
        "missing_phone": "Укажите номер телефона в профиле или передайте его в запросе.",
    }

    def validate(self, attrs):
        user = self.context["request"].user
        phone = (attrs.get("phone") or "").strip() or (user.phone or "").strip()
        if not phone:
            raise serializers.ValidationError(
                {"phone": self.error_messages["missing_phone"]}
            )
        attrs["phone"] = phone
        return attrs


class PhoneConfirmationConfirmSerializer(serializers.Serializer):
    code = serializers.CharField()

    default_error_messages = {
        "invalid_code": "Код подтверждения телефона недействителен или устарел.",
        "already_verified": "Телефон уже подтвержден.",
    }

    def validate(self, attrs):
        user = self.context["request"].user
        if user.is_phone_verified:
            raise serializers.ValidationError(
                {"code": self.error_messages["already_verified"]}
            )

        confirmation = (
            PhoneConfirmation.objects.filter(user=user, consumed_at__isnull=True)
            .order_by("-created_at", "-id")
            .first()
        )
        if confirmation is None or confirmation.is_expired:
            raise serializers.ValidationError(
                {"code": self.error_messages["invalid_code"]}
            )

        confirmation.attempt_count += 1
        confirmation.save(update_fields=["attempt_count"])

        if not confirmation.check_code(attrs["code"]):
            raise serializers.ValidationError(
                {"code": self.error_messages["invalid_code"]}
            )

        self.context["confirmation"] = confirmation
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        confirmation = self.context["confirmation"]
        confirmation.consumed_at = timezone.now()
        confirmation.save(update_fields=["consumed_at"])
        if user.phone != confirmation.phone:
            user.phone = confirmation.phone
            user.save(update_fields=["phone"])
        user.mark_phone_verified()
        return user
