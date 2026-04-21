from decimal import Decimal

from rest_framework.exceptions import ValidationError

from delivery.models import DeliveryMethod, OrderDeliverySnapshot


def get_available_delivery_methods():
    return DeliveryMethod.objects.filter(is_active=True).order_by("sort_order", "name")


def resolve_delivery_method(code=None):
    methods = get_available_delivery_methods()
    if code:
        try:
            return methods.get(code=code)
        except DeliveryMethod.DoesNotExist as exc:
            raise ValidationError(
                {
                    "delivery_method_code": {
                        "code": "delivery_method_unavailable",
                        "message": "Способ доставки недоступен.",
                    }
                }
            ) from exc
    return methods.first()


def delivery_price_for(method):
    if method is None:
        return Decimal("0.00")
    return method.price_amount


def create_order_delivery_snapshot(order, method, shipping_data):
    if method is None:
        return None
    return OrderDeliverySnapshot.objects.create(
        order=order,
        delivery_method=method,
        method_code=method.code,
        method_name=method.name,
        method_kind=method.kind,
        price_amount=method.price_amount,
        currency=method.currency,
        estimated_days_min=method.estimated_days_min,
        estimated_days_max=method.estimated_days_max,
        recipient_name=shipping_data["shipping_name"],
        recipient_phone=shipping_data["shipping_phone"],
        country=shipping_data["shipping_country"],
        city=shipping_data["shipping_city"],
        postal_code=shipping_data["shipping_postal_code"],
        line1=shipping_data["shipping_line1"],
        line2=shipping_data.get("shipping_line2", ""),
    )
