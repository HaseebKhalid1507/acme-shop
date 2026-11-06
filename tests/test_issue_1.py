"""Regression test for acme-shop#1.

Applying an empty coupon code (or any unknown code) must raise ValueError,
NOT crash with a KeyError propagating from pricing.apply_coupon().
"""
import pytest
from shop.pricing import apply_coupon
from shop.catalog import Catalog
from shop.cart import Cart


def test_empty_coupon_code_raises_value_error():
    """apply_coupon with '' must raise ValueError, not KeyError."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "")


def test_unknown_coupon_code_raises_value_error():
    """apply_coupon with an unrecognised code must raise ValueError."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "DOESNOTEXIST")


def test_cart_total_raises_value_error_on_empty_coupon():
    """cart.total() must raise ValueError (not KeyError) when blank coupon applied."""
    cart = Cart(Catalog.default())
    cart.add("SKU-001", qty=1)
    cart.apply_coupon("")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_unaffected_after_valid_coupon():
    """Valid coupon still works after the fix."""
    cart = Cart(Catalog.default())
    cart.add("SKU-002", qty=1)   # 49.99
    cart.apply_coupon("SAVE10")
    breakdown = cart.total()
    assert breakdown["discount"] == pytest.approx(round(49.99 * 0.10, 2))
