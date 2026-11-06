"""Regression test for acme-shop#1.

An empty coupon code (or any unknown code) must raise ValueError, not KeyError.
Calling cart.total() after apply_coupon("") must not crash.
"""
import pytest
from shop.catalog import Catalog, Product
from shop.cart import Cart
from shop.pricing import apply_coupon


# --- unit-level: apply_coupon itself ------------------------------------------

def test_apply_coupon_empty_string_raises_value_error():
    """Empty code must raise ValueError (not KeyError, not crash)."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "")


def test_apply_coupon_unknown_code_raises_value_error():
    """Unknown code must raise ValueError."""
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "DOESNOTEXIST")


def test_apply_coupon_valid_code_still_works():
    """Valid codes must still apply correctly."""
    discounted, discount = apply_coupon(100.0, "SAVE10")
    assert discount == pytest.approx(10.0)
    assert discounted == pytest.approx(90.0)


# --- integration-level: cart.total() does not crash ---------------------------

def _make_cart() -> Cart:
    cat = Catalog([Product(id="A", name="Widget", price=50.0, stock=10)])
    cart = Cart(cat)
    cart.add("A", qty=2)   # subtotal = 100.0
    return cart


def test_cart_total_empty_coupon_raises_value_error():
    """cart.total() after apply_coupon('') must raise ValueError, not crash."""
    cart = _make_cart()
    cart.apply_coupon("")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_unknown_coupon_raises_value_error():
    """cart.total() with an unknown coupon must raise ValueError."""
    cart = _make_cart()
    cart.apply_coupon("BOGUS")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_no_coupon_unaffected():
    """Carts without a coupon must still compute totals correctly."""
    cart = _make_cart()
    result = cart.total()
    assert result["subtotal"] == pytest.approx(100.0)
    assert result["discount"] == pytest.approx(0.0)
