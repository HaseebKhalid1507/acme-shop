"""Regression test for acme-shop#1.

An empty coupon code (or any unknown code) must raise ValueError, not KeyError.
Cart.total() with a blank coupon must not crash.
"""
import pytest
from shop.catalog import Catalog, Product
from shop.cart import Cart
from shop.pricing import apply_coupon


class TestIssue1ApplyCoupon:
    def test_empty_code_raises_value_error(self):
        """apply_coupon with '' must raise ValueError, not KeyError."""
        with pytest.raises(ValueError, match="coupon"):
            apply_coupon(100.0, "")

    def test_unknown_code_raises_value_error(self):
        """apply_coupon with an unrecognised code must raise ValueError."""
        with pytest.raises(ValueError, match="coupon"):
            apply_coupon(100.0, "DOESNOTEXIST")

    def test_valid_code_still_works(self):
        """Known coupon codes must still apply correctly."""
        result, discount = apply_coupon(100.0, "SAVE10")
        assert discount == pytest.approx(10.0)
        assert result == pytest.approx(90.0)


class TestIssue1CartTotal:
    def _make_cart(self):
        cat = Catalog([Product("P1", "Widget", 50.0, 10)])
        cart = Cart(cat)
        cart.add("P1", 1)
        return cart

    def test_blank_coupon_raises_value_error(self):
        """Cart.total() with an empty coupon must raise ValueError, not crash with KeyError."""
        cart = self._make_cart()
        cart.apply_coupon("")
        with pytest.raises(ValueError, match="coupon"):
            cart.total()

    def test_unknown_coupon_raises_value_error(self):
        """Cart.total() with an unknown coupon must raise ValueError."""
        cart = self._make_cart()
        cart.apply_coupon("BOGUS")
        with pytest.raises(ValueError, match="coupon"):
            cart.total()

    def test_no_coupon_still_works(self):
        """Cart.total() without a coupon must succeed."""
        cart = self._make_cart()
        result = cart.total()
        assert result["discount"] == 0.0
        assert result["total"] > 0
