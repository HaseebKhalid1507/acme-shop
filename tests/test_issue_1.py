"""Regression test for acme-shop#1.

Applying an empty or unknown coupon code must raise ValueError, not crash
with a KeyError propagating from the pricing module.
"""
import pytest
from shop.pricing import apply_coupon
from shop.cart import Cart
from shop.catalog import Catalog


# ---------------------------------------------------------------------------
# pricing.apply_coupon — the root-cause function
# ---------------------------------------------------------------------------

def test_empty_coupon_code_raises_value_error():
    """apply_coupon('') must raise ValueError, not KeyError."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "")


def test_unknown_coupon_code_raises_value_error():
    """apply_coupon with an unknown code must raise ValueError, not KeyError."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "DOESNOTEXIST")


# ---------------------------------------------------------------------------
# cart.total() — the caller that surfaces the crash in production
# ---------------------------------------------------------------------------

def _make_cart() -> Cart:
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-001", 1)
    return cart


def test_cart_total_with_empty_coupon_raises_value_error():
    """cart.total() must raise ValueError when an empty coupon was applied."""
    cart = _make_cart()
    cart.apply_coupon("")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_with_unknown_coupon_raises_value_error():
    """cart.total() must raise ValueError for an unknown coupon code."""
    cart = _make_cart()
    cart.apply_coupon("BOGUS")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_unaffected_after_bad_coupon():
    """After a bad coupon is set, clearing and re-totalling without coupon works."""
    cart = _make_cart()
    cart.apply_coupon("")
    # Catch the error, then clear the coupon and proceed normally
    with pytest.raises(ValueError):
        cart.total()
    cart.apply_coupon(None)   # type: ignore[arg-type]  — None means "no coupon"
    result = cart.total()
    assert result["total"] > 0
