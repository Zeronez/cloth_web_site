from dataclasses import dataclass

import pytest

from _contract_imports import get_field, import_contract_module, require_attrs


cart_services = import_contract_module(
    "cart.services",
    "apps.cart.services",
    "shop.cart.services",
)

CartLineInput, CartValidationError, build_cart_snapshot = require_attrs(
    cart_services,
    "CartLineInput",
    "CartValidationError",
    "build_cart_snapshot",
)


@dataclass(frozen=True)
class VariantStub:
    id: int
    sku: str
    unit_price_cents: int
    stock_quantity: int
    reserved_quantity: int = 0
    is_active: bool = True


def variant_lookup(variants):
    return {variant.id: variant for variant in variants}.__getitem__


def test_build_cart_snapshot_merges_duplicate_lines_and_totals_subtotal():
    lookup = variant_lookup(
        [
            VariantStub(
                id=101,
                sku="tee-naruto-m",
                unit_price_cents=1500,
                stock_quantity=10,
            )
        ]
    )

    snapshot = build_cart_snapshot(
        [
            CartLineInput(variant_id=101, quantity=2),
            CartLineInput(variant_id=101, quantity=3),
        ],
        variant_lookup=lookup,
    )

    assert get_field(snapshot, "total_quantity") == 5
    assert get_field(snapshot, "subtotal_cents") == 7500

    items = get_field(snapshot, "items")
    assert len(items) == 1
    assert get_field(items[0], "variant_id") == 101
    assert get_field(items[0], "quantity") == 5
    assert get_field(items[0], "unit_price_cents") == 1500
    assert get_field(items[0], "line_total_cents") == 7500


@pytest.mark.parametrize("quantity", [0, -1])
def test_build_cart_snapshot_rejects_non_positive_quantities(quantity):
    lookup = variant_lookup(
        [
            VariantStub(
                id=101,
                sku="tee-naruto-m",
                unit_price_cents=1500,
                stock_quantity=10,
            )
        ]
    )

    with pytest.raises(CartValidationError):
        build_cart_snapshot(
            [CartLineInput(variant_id=101, quantity=quantity)],
            variant_lookup=lookup,
        )


def test_build_cart_snapshot_rejects_unknown_variant():
    def missing_variant_lookup(variant_id):
        raise KeyError(variant_id)

    with pytest.raises(CartValidationError):
        build_cart_snapshot(
            [CartLineInput(variant_id=404, quantity=1)],
            variant_lookup=missing_variant_lookup,
        )


def test_build_cart_snapshot_rejects_inactive_variant():
    lookup = variant_lookup(
        [
            VariantStub(
                id=101,
                sku="tee-naruto-m",
                unit_price_cents=1500,
                stock_quantity=10,
                is_active=False,
            )
        ]
    )

    with pytest.raises(CartValidationError):
        build_cart_snapshot(
            [CartLineInput(variant_id=101, quantity=1)],
            variant_lookup=lookup,
        )
