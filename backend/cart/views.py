from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cart.models import CartItem
from cart.serializers import (
    AddCartItemSerializer,
    CartSerializer,
    SetCartItemQuantitySerializer,
)
from cart.services import (
    add_variant_to_cart,
    get_or_create_cart,
    set_cart_item_quantity,
)


class CartViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CartSerializer

    def get_queryset(self):
        cart = get_or_create_cart(self.request)
        return (
            type(cart)
            .objects.filter(pk=cart.pk)
            .prefetch_related(
                "items__variant__product", "items__variant__product__images"
            )
        )

    def list(self, request, *args, **kwargs):
        cart = self.get_queryset().first()
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_or_create_cart(request)
        add_variant_to_cart(cart, **serializer.validated_data)
        cart.refresh_from_db()
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["patch", "delete"],
        url_path=r"items/(?P<item_id>\d+)",
    )
    def item_detail(self, request, item_id=None):
        cart = get_or_create_cart(request)
        if request.method == "PATCH":
            serializer = SetCartItemQuantitySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            set_cart_item_quantity(cart, item_id, serializer.validated_data["quantity"])
        else:
            item = get_object_or_404(CartItem, pk=item_id, cart=cart)
            item.delete()
        cart.refresh_from_db()
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )
