from dataclasses import dataclass

import pytest

from _contract_imports import import_contract_module, require_attrs


stock_services = import_contract_module(
    "inventory.services",
    "stock.services",
    "apps.inventory.services",
    "shop.inventory.services",
)

StockValidationError, available_to_sell, ensure_can_fulfill = require_attrs(
    stock_services,
    "StockValidationError",
    "available_to_sell",
    "ensure_can_fulfill",
)


@dataclass(frozen=True)
class StockVariantStub:
    id: int
    sku: str
    stock_quantity: int
    reserved_quantity: int = 0
    is_active: bool = True


@pytest.mark.parametrize(
    ("stock_quantity", "reserved_quantity", "expected"),
    [
        (12, 0, 12),
        (12, 5, 7),
        (3, 9, 0),
    ],
)
def test_available_to_sell_subtracts_reservations_and_never_goes_negative(
    stock_quantity,
    reserved_quantity,
    expected,
):
    variant = StockVariantStub(
        id=201,
        sku="hoodie-luffy-l",
        stock_quantity=stock_quantity,
        reserved_quantity=reserved_quantity,
    )

    assert available_to_sell(variant) == expected


def test_ensure_can_fulfill_allows_active_variant_with_enough_sellable_stock():
    variant = StockVariantStub(
        id=201,
        sku="hoodie-luffy-l",
        stock_quantity=12,
        reserved_quantity=2,
    )

    assert ensure_can_fulfill(variant, requested_quantity=10) is None


@pytest.mark.parametrize(
    "variant",
    [
        StockVariantStub(
            id=201,
            sku="hoodie-luffy-l",
            stock_quantity=12,
            reserved_quantity=0,
            is_active=False,
        ),
        StockVariantStub(
            id=202,
            sku="tee-evangelion-s",
            stock_quantity=4,
            reserved_quantity=1,
            is_active=True,
        ),
    ],
)
def test_ensure_can_fulfill_rejects_inactive_or_insufficient_stock(variant):
    with pytest.raises(StockValidationError):
        ensure_can_fulfill(variant, requested_quantity=5)


@pytest.mark.parametrize("requested_quantity", [0, -1])
def test_ensure_can_fulfill_rejects_non_positive_requested_quantity(
    requested_quantity,
):
    variant = StockVariantStub(
        id=201,
        sku="hoodie-luffy-l",
        stock_quantity=12,
        reserved_quantity=0,
    )

    with pytest.raises(StockValidationError):
        ensure_can_fulfill(variant, requested_quantity=requested_quantity)
