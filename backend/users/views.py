import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from config.permissions import IsObjectOwner
from users.models import Address
from users.serializers import (
    AddressSerializer,
    BruteForceAwareTokenObtainPairSerializer,
    DeleteAccountSerializer,
    EmailConfirmationConfirmSerializer,
    FitProfileSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PhoneConfirmationConfirmSerializer,
    PhoneConfirmationRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from users.security import (
    record_password_reset_request,
    should_suppress_password_reset_request,
)
from users.services import build_account_export_payload, delete_customer_account
from users.tasks import (
    send_email_confirmation_email,
    send_password_reset_email,
    send_phone_confirmation_sms,
)
from users.models import PhoneConfirmation


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "privacy_policy_version": settings.PRIVACY_POLICY_VERSION,
                "offer_agreement_version": settings.OFFER_AGREEMENT_VERSION,
                "marketing_consent_version": settings.MARKETING_CONSENT_VERSION,
            }
        )
        return context

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email:
            transaction.on_commit(lambda: send_email_confirmation_email.delay(user.id))
        response_serializer = UserSerializer(
            user,
            context={
                "request": request,
                "marketing_consent_version": settings.MARKETING_CONSENT_VERSION,
            },
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        serializer.save()


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["marketing_consent_version"] = settings.MARKETING_CONSENT_VERSION
        return context

    def get_object(self):
        return self.request.user


class UserFitProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = FitProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(self.get_serializer(self.get_object()).data)


class AccountExportView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "auth"

    @extend_schema(responses={200: None})
    def get(self, request):
        payload = build_account_export_payload(
            user=request.user,
            serializer_context={"request": request},
        )
        return Response(payload, status=status.HTTP_200_OK)


class AccountDeleteView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "auth"

    @extend_schema(request=DeleteAccountSerializer, responses={200: None})
    def post(self, request):
        serializer = DeleteAccountSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        result = delete_customer_account(user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated, IsObjectOwner)
    owner_field = "user"
    throttle_scope = "cart"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)


@extend_schema(request=None, responses={204: None})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh = request.data.get("refresh")
    if not refresh:
        raise ValidationError({"refresh": "Refresh token is required."})

    try:
        token = RefreshToken(refresh)
    except TokenError as exc:
        raise ValidationError({"refresh": "Refresh token is invalid."}) from exc

    token_user_id = str(token.get("user_id", ""))
    if token_user_id != str(request.user.pk):
        raise ValidationError({"refresh": "Refresh token is invalid."})

    token.blacklist()
    return Response(status=status.HTTP_204_NO_CONTENT)


class ScopedTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"
    serializer_class = BruteForceAwareTokenObtainPairSerializer


class ScopedTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(
        auth=[],
        request=PasswordResetRequestSerializer,
        responses={202: None},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if should_suppress_password_reset_request(email):
            return Response(status=status.HTTP_202_ACCEPTED)

        record_password_reset_request(email)
        user = User.objects.filter(email__iexact=email).exclude(email="").first()
        if user is not None:
            transaction.on_commit(lambda: send_password_reset_email.delay(user.id))
        return Response(status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(
        auth=[],
        request=PasswordResetConfirmSerializer,
        responses={200: UserSerializer},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


class EmailConfirmationRequestView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "auth"

    @extend_schema(request=None, responses={202: None})
    def post(self, request):
        if request.user.email and not request.user.is_email_verified:
            transaction.on_commit(
                lambda: send_email_confirmation_email.delay(request.user.id)
            )
        return Response(status=status.HTTP_202_ACCEPTED)


class EmailConfirmationConfirmView(APIView):
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(
        auth=[],
        request=EmailConfirmationConfirmSerializer,
        responses={200: UserSerializer},
    )
    def post(self, request):
        serializer = EmailConfirmationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


class PhoneConfirmationRequestView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "auth"

    @extend_schema(request=PhoneConfirmationRequestSerializer, responses={202: None})
    def post(self, request):
        serializer = PhoneConfirmationRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        code = getattr(settings, "AUTH_PHONE_CONFIRMATION_TEST_CODE", None)
        if not code:
            code = f"{secrets.randbelow(1_000_000):06d}"

        confirmation = PhoneConfirmation(
            user=request.user,
            phone=phone,
            expires_at=timezone.now()
            + timedelta(
                minutes=getattr(settings, "AUTH_PHONE_CONFIRMATION_TTL_MINUTES", 10)
            ),
        )
        confirmation.set_code(code)
        confirmation.save()

        transaction.on_commit(
            lambda: send_phone_confirmation_sms.delay(
                user_id=request.user.id, phone=phone, code=code
            )
        )
        return Response(status=status.HTTP_202_ACCEPTED)


class PhoneConfirmationConfirmView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "auth"

    @extend_schema(
        request=PhoneConfirmationConfirmSerializer, responses={200: UserSerializer}
    )
    def post(self, request):
        serializer = PhoneConfirmationConfirmSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)
