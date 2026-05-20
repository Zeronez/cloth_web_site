from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from pricing.models import Coupon, CouponRedemption


_MONEY_QUANT = Decimal("0.01")


def _quantize(amount: Decimal) -> Decimal:
    return (amount or Decimal("0.00")).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Totals:
    currency: str
    items_subtotal: Decimal
    discount: Decimal
    delivery: Decimal
    tax: Decimal
    total: Decimal


def compute_totals(
    *,
    currency: str,
    items_subtotal: Decimal,
    delivery: Decimal,
    coupon: Coupon | None = None,
    user=None,
    now=None,
):
    now = now or timezone.now()
    items_subtotal = _quantize(items_subtotal)
    delivery = _quantize(delivery)
    tax = Decimal("0.00")
    discount = Decimal("0.00")

    if coupon is not None:
        if coupon.currency != currency:
            raise ValidationError(
                {
                    "coupon": {
                        "code": "currency_mismatch",
                        "message": "Купон в другой валюте.",
                    }
                }
            )
        if not coupon.is_currently_active(now=now):
            raise ValidationError(
                {"coupon": {"code": "coupon_inactive", "message": "Купон недоступен."}}
            )
        if items_subtotal < coupon.min_cart_amount:
            raise ValidationError(
                {
                    "coupon": {
                        "code": "min_cart_not_met",
                        "message": "Сумма корзины меньше минимума по купону.",
                    }
                }
            )

        if coupon.kind == Coupon.Kind.FIXED:
            discount = min(_quantize(coupon.amount), items_subtotal)
        elif coupon.kind == Coupon.Kind.PERCENT:
            percent = max(0, min(int(coupon.percent or 0), 100))
            discount = _quantize((items_subtotal * Decimal(percent)) / Decimal(100))
        elif coupon.kind == Coupon.Kind.FREE_SHIPPING:
            discount = Decimal("0.00")
            delivery = Decimal("0.00")

        if user is not None and coupon.per_user_limit:
            used_count = CouponRedemption.objects.filter(
                coupon=coupon, user=user
            ).count()
            if used_count >= coupon.per_user_limit:
                raise ValidationError(
                    {
                        "coupon": {
                            "code": "per_user_limit_reached",
                            "message": "Лимит использования купона исчерпан.",
                        }
                    }
                )

    total = _quantize(items_subtotal - discount + delivery + tax)
    return Totals(
        currency=currency,
        items_subtotal=_quantize(items_subtotal),
        discount=_quantize(discount),
        delivery=_quantize(delivery),
        tax=_quantize(tax),
        total=_quantize(total),
    )


@transaction.atomic
def redeem_coupon(*, coupon: Coupon, user, order=None):
    CouponRedemption.objects.create(coupon=coupon, user=user, order=order)
    Coupon.objects.filter(pk=coupon.pk).update(redeemed_count=F("redeemed_count") + 1)
