from decimal import Decimal

import pytest

from catalog.models import ProductPriceHistory


pytestmark = pytest.mark.django_db


def test_sale_price_is_used_for_variant_price(product_factory):
    product = product_factory(
        name="Sale Tee",
        base_price="100.00",
        variants=[
            {
                "sku": "SALE-TEE-M",
                "size": "M",
                "color": "Black",
                "stock_quantity": 5,
                "price_delta": "0.00",
            }
        ],
    )
    product.sale_price = Decimal("55.00")
    product.save(update_fields=["sale_price", "updated_at"])
    variant = product.variants.get()
    assert variant.price == Decimal("55.00")


def test_product_price_history_records_base_price_change(product_factory):
    product = product_factory(name="History Tee", base_price="10.00")
    product.base_price = Decimal("12.00")
    product.save(update_fields=["base_price", "updated_at"])

    assert ProductPriceHistory.objects.filter(
        product=product,
        field_name="base_price",
        old_value=Decimal("10.00"),
        new_value=Decimal("12.00"),
    ).exists()
