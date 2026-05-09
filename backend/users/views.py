from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Address
from users.serializers import AddressSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)
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
    throttle_scope = "auth"


class ScopedTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth"
