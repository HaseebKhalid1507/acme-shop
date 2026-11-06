"""Tests for acme-shop#1: empty/blank coupon code crashes checkout.

An empty or unknown coupon code should raise ValueError, not KeyError/crash.
"""
import pytest
from shop.pricing import apply_coupon
from shop.cart import Cart
from shop.catalog import Catalog


def _make_cart() -> Cart:
    catalog = Catalog.default()
    cart = Cart(catalog)
    # Add at least one item so subtotal > 0
    products = catalog.all()
    cart.add(products[0].id, 1)
    return cart


# --- pricing.apply_coupon ---------------------------------------------------

def test_apply_coupon_empty_string_raises():
    """Empty coupon code must raise ValueError, not KeyError."""
    with pytest.raises(ValueError):
        apply_coupon(100.0, "")


def test_apply_coupon_blank_whitespace_raises():
    """Whitespace-only coupon code must raise ValueError."""
    with pytest.raises(ValueError):
        apply_coupon(100.0, "   ")


def test_apply_coupon_unknown_code_raises():
    """Unknown coupon code must raise ValueError, not KeyError."""
    with pytest.raises(ValueError):
        apply_coupon(100.0, "DOESNOTEXIST")


def test_apply_coupon_valid_still_works():
    """Valid coupon code must still apply correctly."""
    result_subtotal, discount = apply_coupon(100.0, "SAVE10")
    assert discount == pytest.approx(10.0)
    assert result_subtotal == pytest.approx(90.0)


# --- Cart.total() via apply_coupon path ------------------------------------

def test_cart_total_empty_coupon_raises():
    """Cart.total() with an empty coupon must raise ValueError, not crash."""
    cart = _make_cart()
    cart.apply_coupon("")
    with pytest.raises(ValueError):
        cart.total()


def test_cart_total_unknown_coupon_raises():
    """Cart.total() with an unknown coupon must raise ValueError."""
    cart = _make_cart()
    cart.apply_coupon("FAKECODE99")
    with pytest.raises(ValueError):
        cart.total()


def test_cart_total_no_coupon_unaffected():
    """Cart.total() with no coupon still works correctly."""
    cart = _make_cart()
    result = cart.total()
    assert result["total"] > 0
    assert result["discount"] == 0.0
