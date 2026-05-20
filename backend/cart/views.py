from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cart.models import Cart, CartItem
from cart.serializers import (
    AddCartItemSerializer,
    ApplyCouponSerializer,
    CartSerializer,
    QuoteTotalsSerializer,
    SetCartItemQuantitySerializer,
)
from cart.services import (
    add_variant_to_cart,
    get_or_create_cart,
    set_cart_item_quantity,
)
from delivery.services import delivery_price_for, resolve_delivery_method
from pricing.models import Coupon
from pricing.services import compute_totals


class CartViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "cart"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
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

    @action(detail=False, methods=["post"], url_path="items", throttle_scope="cart")
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
        throttle_scope="cart",
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

    @action(
        detail=False,
        methods=["post", "delete"],
        url_path="coupon",
        throttle_scope="cart",
    )
    def coupon(self, request):
        cart = get_or_create_cart(request)
        if request.method == "DELETE":
            cart.coupon = None
            cart.save(update_fields=["coupon", "updated_at"])
            cart.refresh_from_db()
            return Response(
                CartSerializer(cart, context=self.get_serializer_context()).data
            )

        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["coupon_code"]
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon is None:
            raise ValidationError({"coupon_code": "Купон не найден."})

        user = (
            request.user if getattr(request.user, "is_authenticated", False) else None
        )
        compute_totals(
            currency="RUB",
            items_subtotal=cart.total_amount,
            delivery=0,
            coupon=coupon,
            user=user,
        )
        cart.coupon = coupon
        cart.save(update_fields=["coupon", "updated_at"])
        cart.refresh_from_db()
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )

    @action(detail=False, methods=["post"], url_path="quote", throttle_scope="checkout")
    def quote(self, request):
        serializer = QuoteTotalsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_or_create_cart(request)

        delivery_amount = 0
        method_code = serializer.validated_data.get("delivery_method_code") or ""
        if method_code:
            method = resolve_delivery_method(
                method_code,
                country=serializer.validated_data.get("shipping_country", ""),
                city=serializer.validated_data.get("shipping_city", ""),
                postal_code=serializer.validated_data.get("shipping_postal_code", ""),
            )
            delivery_amount = delivery_price_for(
                method,
                country=serializer.validated_data.get("shipping_country", ""),
                city=serializer.validated_data.get("shipping_city", ""),
                postal_code=serializer.validated_data.get("shipping_postal_code", ""),
            )

        coupon = cart.coupon
        coupon_code = (serializer.validated_data.get("coupon_code") or "").strip()
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if coupon is None:
                raise ValidationError({"coupon_code": "Купон не найден."})

        user = (
            request.user if getattr(request.user, "is_authenticated", False) else None
        )
        totals = compute_totals(
            currency="RUB",
            items_subtotal=cart.total_amount,
            delivery=delivery_amount,
            coupon=coupon,
            user=user,
        )
        return Response(
            {
                "currency": totals.currency,
                "items_subtotal_amount": str(totals.items_subtotal),
                "discount_amount": str(totals.discount),
                "delivery_amount": str(totals.delivery),
                "tax_amount": str(totals.tax),
                "fiscal_fee_amount": "0.00",
                "total_amount": str(totals.total),
                "coupon_code": coupon.code if coupon else "",
            }
        )
