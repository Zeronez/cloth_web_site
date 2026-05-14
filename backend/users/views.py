from django.contrib.auth import get_user_model
from django.db import transaction
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
    EmailConfirmationConfirmSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from users.tasks import send_email_confirmation_email, send_password_reset_email


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()
        if user.email:
            transaction.on_commit(lambda: send_email_confirmation_email.delay(user.id))


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


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
        user = (
            User.objects.filter(email__iexact=serializer.validated_data["email"])
            .exclude(email="")
            .first()
        )
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
        serializer = PasswordResetConfirmSerializer(data=request.data)
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
