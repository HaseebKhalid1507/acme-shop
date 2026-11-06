"""Tests for pricing — exercises valid coupons only."""
import pytest
from shop.pricing import apply_coupon, apply_tax, TAX_RATE, COUPONS


def test_tax_rate_applied():
    assert apply_tax(100.0) == 108.0


def test_tax_zero_input():
    assert apply_tax(0.0) == 0.0


@pytest.mark.parametrize("code,rate", list(COUPONS.items()))
def test_valid_coupon(code, rate):
    discounted, discount = apply_coupon(100.0, code)
    assert discount == pytest.approx(100.0 * rate)
    assert discounted == pytest.approx(100.0 - discount)


def test_coupon_on_fractional_amount():
    discounted, discount = apply_coupon(49.99, "SAVE10")
    assert discount == pytest.approx(4.999)
    assert discounted == pytest.approx(44.991)
