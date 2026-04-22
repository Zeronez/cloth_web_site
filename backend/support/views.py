from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from support.models import ContactRequest
from support.serializers import ContactRequestSerializer


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ContactRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ContactRequest.objects.none()
    serializer_class = ContactRequestSerializer
    permission_classes = (AllowAny,)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(
            user=user,
            ip_address=_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255],
        )


# Create your views here.
