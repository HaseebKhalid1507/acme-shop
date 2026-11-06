"""Tests for acme-shop#2: tax applied twice on coupon orders.

price_after_discount_and_tax() must not embed tax in its return value,
because callers (Cart.total, checkout, receipt) also apply tax.  The result
should be the post-discount subtotal only; apply_tax() is the caller's
responsibility.
"""
import pytest
from shop.pricing import (
    apply_coupon,
    apply_tax,
    price_after_discount_and_tax,
    TAX_RATE,
)
from shop.catalog import Catalog
from shop.cart import Cart


# ---------------------------------------------------------------------------
# price_after_discount_and_tax must return post-discount subtotal (NO tax)
# ---------------------------------------------------------------------------

def test_price_after_discount_and_tax_with_coupon_no_double_tax():
    """With a coupon, the return value must be the discounted subtotal only.

    If the function bakes tax in, applying apply_tax() on its return doubles
    the tax — the exact customer-facing overcharge described in acme-shop#2.
    """
    subtotal = 100.0
    post_discount = price_after_discount_and_tax(subtotal, "SAVE10")
    # Should be 90.0 (subtotal - 10% discount), NOT 97.20 (already including tax)
    assert post_discount == pytest.approx(90.0), (
        f"Expected post-discount subtotal 90.0, got {post_discount}. "
        "Function must not embed tax."
    )


def test_price_after_discount_and_tax_no_coupon_no_double_tax():
    """Without a coupon the return value is the raw subtotal (no tax baked in)."""
    subtotal = 100.0
    result = price_after_discount_and_tax(subtotal, None)
    assert result == pytest.approx(100.0), (
        f"Expected unchanged subtotal 100.0, got {result}. "
        "Function must not embed tax."
    )


def test_price_after_discount_and_tax_composable_with_apply_tax():
    """Composing price_after_discount_and_tax with apply_tax gives correct total."""
    subtotal = 100.0
    post_discount = price_after_discount_and_tax(subtotal, "SAVE10")
    total = apply_tax(post_discount)
    # 10% off 100 => 90, then 8% tax => 97.20
    assert total == pytest.approx(97.20)


# ---------------------------------------------------------------------------
# Cart.total() must compute tax on post-discount subtotal (once only)
# ---------------------------------------------------------------------------

def _make_cart_with_coupon(product_id: str, qty: int, coupon: str) -> Cart:
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add(product_id, qty)
    cart.apply_coupon(coupon)
    return cart


def test_cart_total_tax_on_discounted_subtotal():
    """Tax in cart.total() must be computed on the post-discount subtotal."""
    cart = _make_cart_with_coupon("SKU-001", 1, "SAVE10")  # $19.99
    t = cart.total()
    raw = t["subtotal"]          # 19.99
    discount = t["discount"]
    expected_post_discount = round(raw - discount, 2)
    expected_tax = round(expected_post_discount * TAX_RATE, 2)
    assert t["tax"] == pytest.approx(expected_tax, abs=0.01), (
        f"Tax should be on post-discount subtotal ({expected_post_discount}), "
        f"got {t['tax']} (expected {expected_tax})."
    )


def test_cart_total_tax_not_on_full_subtotal():
    """Tax must NOT equal 8% of the pre-discount subtotal when coupon is applied."""
    cart = _make_cart_with_coupon("SKU-002", 1, "SAVE20")  # $49.99, 20% off
    t = cart.total()
    raw = t["subtotal"]  # 49.99
    tax_on_full = round(raw * TAX_RATE, 2)
    assert t["tax"] != pytest.approx(tax_on_full), (
        "Tax is being charged on the pre-discount subtotal — that is the bug."
    )


def test_cart_total_no_double_tax_vs_manual():
    """cart.total()['total'] must equal apply_tax(post_discount_subtotal)."""
    cart = _make_cart_with_coupon("SKU-004", 1, "HALFOFF")  # $99.99, 50% off
    t = cart.total()
    raw = t["subtotal"]                     # 99.99
    post_discount = round(raw * 0.50, 2)    # 49.995 → 50.0 (rounded)
    expected_total = apply_tax(raw - t["discount"])
    assert t["total"] == pytest.approx(expected_total, abs=0.02)
