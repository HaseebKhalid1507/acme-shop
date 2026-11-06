"""Regression test for acme-shop#2.

Tax must be calculated on the post-discount subtotal exactly once.
The breakdown returned by cart.total() must satisfy:
  subtotal + tax == total   (all three fields internally consistent)
And the Order record from checkout must carry the same invariant.
"""
import pytest
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout
from shop.pricing import price_after_discount_and_tax, TAX_RATE


@pytest.fixture
def cart_with_coupon():
    cat = Catalog.default()
    cart = Cart(cat)
    cart.add("SKU-002", 1)   # Gadget Deluxe $49.99
    cart.apply_coupon("SAVE10")
    return cart


# --- cart.total() internal consistency ----------------------------------------

def test_total_subtotal_is_post_discount(cart_with_coupon):
    """subtotal in breakdown must be the post-discount (tax base) amount."""
    t = cart_with_coupon.total()
    raw = cart_with_coupon.raw_subtotal()         # 49.99
    expected_post_discount = round(raw - t["discount"], 2)  # 49.99 - 5.00 = 44.99
    assert t["subtotal"] == pytest.approx(expected_post_discount), (
        "subtotal should be post-discount so subtotal + tax == total"
    )


def test_total_fields_add_up(cart_with_coupon):
    """subtotal + tax must equal total — no hidden double-tax."""
    t = cart_with_coupon.total()
    assert round(t["subtotal"] + t["tax"], 2) == pytest.approx(t["total"]), (
        "subtotal + tax != total: tax is being applied to the wrong base"
    )


def test_tax_computed_on_discounted_amount(cart_with_coupon):
    """Tax line must equal subtotal * TAX_RATE, not raw_subtotal * TAX_RATE."""
    t = cart_with_coupon.total()
    expected_tax = round(t["subtotal"] * TAX_RATE, 2)
    assert t["tax"] == pytest.approx(expected_tax)


def test_total_no_coupon_still_consistent():
    """Without coupon, subtotal + tax must still equal total."""
    cat = Catalog.default()
    cart = Cart(cat)
    cart.add("SKU-003", 3)   # 3 * 9.99 = 29.97
    t = cart.total()
    assert round(t["subtotal"] + t["tax"], 2) == pytest.approx(t["total"])


# --- checkout Order consistency -----------------------------------------------

def test_order_fields_consistent_with_coupon():
    """Order subtotal + tax must equal order total after checkout with coupon."""
    cat = Catalog.default()
    cart = Cart(cat)
    cart.add("SKU-002", 1)
    cart.apply_coupon("SAVE20")
    co = Checkout(cart, cat)
    order = co.place_order()
    assert round(order.subtotal + order.tax, 2) == pytest.approx(order.total), (
        "Order subtotal + tax != total: receipt would show overcharge"
    )


# --- price_after_discount_and_tax agrees with cart.total() --------------------

def test_preview_matches_cart_total():
    """price_after_discount_and_tax() must agree with cart.total()['total']."""
    cat = Catalog.default()
    cart = Cart(cat)
    cart.add("SKU-001", 2)   # 2 * 19.99 = 39.98
    cart.apply_coupon("HALFOFF")
    t = cart.total()
    preview = price_after_discount_and_tax(cart.raw_subtotal(), "HALFOFF")
    assert preview == pytest.approx(t["total"]), (
        "Preview total and cart total disagree — double-tax risk"
    )
