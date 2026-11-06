"""Regression test for acme-shop#1: empty coupon code crashes checkout.

An empty or unknown coupon code must raise ValueError, not KeyError,
and must not crash cart.total().
"""
import pytest
from shop.pricing import apply_coupon
from shop.catalog import Catalog
from shop.cart import Cart


# --- apply_coupon raises ValueError (not KeyError) for empty code ----------

def test_apply_coupon_empty_string_raises_value_error():
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "")


def test_apply_coupon_unknown_code_raises_value_error():
    with pytest.raises(ValueError, match="coupon"):
        apply_coupon(100.0, "DOESNOTEXIST")


# --- cart.total() raises ValueError when blank coupon is applied -----------

@pytest.fixture
def cart():
    return Cart(Catalog.default())


def test_cart_total_empty_coupon_raises_value_error(cart):
    cart.add("SKU-001", 1)
    cart.apply_coupon("")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


def test_cart_total_unknown_coupon_raises_value_error(cart):
    cart.add("SKU-001", 1)
    cart.apply_coupon("BOGUS")
    with pytest.raises(ValueError, match="coupon"):
        cart.total()


# --- valid coupon still works after the fix --------------------------------

def test_apply_coupon_valid_still_works():
    discounted, discount = apply_coupon(100.0, "SAVE10")
    assert discount == pytest.approx(10.0)
    assert discounted == pytest.approx(90.0)
