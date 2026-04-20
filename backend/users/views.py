from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Address
from users.serializers import AddressSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh = request.data.get("refresh")
    if not refresh:
        return Response(
            {"refresh": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token = RefreshToken(refresh)
    token.blacklist()
    return Response(status=status.HTTP_204_NO_CONTENT)
