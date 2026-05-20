from rest_framework import serializers

from cart.models import Cart, CartItem
from catalog.serializers import ProductVariantSerializer
from pricing.services import compute_totals


class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    product = serializers.SerializerMethodField()
    unit_price = serializers.DecimalField(
        source="variant.price", max_digits=12, decimal_places=2, read_only=True
    )
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant",
            "product",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        )

    def get_product(self, obj):
        product = obj.variant.product
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "base_price": str(product.base_price),
            "is_active": product.is_active,
        }


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    currency = serializers.SerializerMethodField()
    items_subtotal_amount = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    delivery_amount = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    fiscal_fee_amount = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    subtotal_amount = serializers.SerializerMethodField()
    coupon_code = serializers.SerializerMethodField()
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = (
            "id",
            "items",
            "currency",
            "items_subtotal_amount",
            "discount_amount",
            "delivery_amount",
            "tax_amount",
            "fiscal_fee_amount",
            "total_amount",
            "subtotal_amount",
            "coupon_code",
            "total_quantity",
            "created_at",
            "updated_at",
        )

    def _totals(self, obj):
        user = getattr(obj, "user", None)
        currency = "RUB"
        items_subtotal = obj.total_amount
        return compute_totals(
            currency=currency,
            items_subtotal=items_subtotal,
            delivery=0,
            coupon=getattr(obj, "coupon", None),
            user=user if user and getattr(user, "is_authenticated", False) else None,
        )

    def get_currency(self, obj):
        return self._totals(obj).currency

    def get_items_subtotal_amount(self, obj):
        return str(self._totals(obj).items_subtotal)

    def get_discount_amount(self, obj):
        return str(self._totals(obj).discount)

    def get_delivery_amount(self, obj):
        return str(self._totals(obj).delivery)

    def get_tax_amount(self, obj):
        return str(self._totals(obj).tax)

    def get_fiscal_fee_amount(self, obj):
        return "0.00"

    def get_total_amount(self, obj):
        return str(self._totals(obj).total)

    def get_subtotal_amount(self, obj):
        return str(self._totals(obj).items_subtotal)

    def get_coupon_code(self, obj):
        coupon = getattr(obj, "coupon", None)
        return coupon.code if coupon else ""


class ApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.SlugField(
        max_length=48, allow_blank=False, trim_whitespace=True
    )


class QuoteTotalsSerializer(serializers.Serializer):
    delivery_method_code = serializers.SlugField(
        max_length=48, required=False, allow_blank=True
    )
    shipping_country = serializers.CharField(
        max_length=80, required=False, allow_blank=True
    )
    shipping_city = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )
    shipping_postal_code = serializers.CharField(
        max_length=32, required=False, allow_blank=True
    )
    coupon_code = serializers.SlugField(
        max_length=48, required=False, allow_blank=True, trim_whitespace=True
    )


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class SetCartItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)
