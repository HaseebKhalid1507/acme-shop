"""Regression test for acme-shop#2.

Tax must be calculated on the post-discount subtotal exactly once.
price_after_discount_and_tax() used to call apply_tax() internally,
which would double-tax any caller that also went through cart.total()
(e.g. a checkout preview endpoint feeding into place_order()).
"""
import pytest
from shop.pricing import price_after_discount_and_tax, apply_tax, TAX_RATE, COUPONS
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout


# ---------------------------------------------------------------------------
# price_after_discount_and_tax must NOT apply tax — it returns post-discount
# subtotal only, so callers (cart.total / checkout) apply tax exactly once.
# ---------------------------------------------------------------------------

def test_price_after_discount_and_tax_no_coupon():
    """No coupon: should return the subtotal unchanged (no tax baked in)."""
    result = price_after_discount_and_tax(100.0, None)
    # Must equal post-discount subtotal with NO extra tax multiplication
    assert result == pytest.approx(100.0)


def test_price_after_discount_and_tax_with_coupon():
    """With coupon: should return post-discount subtotal only (no tax)."""
    result = price_after_discount_and_tax(100.0, "SAVE10")
    # 100 - 10% = 90.0, NOT 90 * 1.08 = 97.20
    assert result == pytest.approx(90.0)


def test_price_after_discount_and_tax_halfoff():
    """HALFOFF coupon: post-discount only, no tax."""
    result = price_after_discount_and_tax(200.0, "HALFOFF")
    assert result == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# End-to-end: checkout total must equal (subtotal - discount) * (1 + TAX_RATE)
# ---------------------------------------------------------------------------

def _checkout_order(sku: str, qty: int, coupon: str | None):
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add(sku, qty=qty)
    if coupon:
        cart.apply_coupon(coupon)
    co = Checkout(cart, catalog)
    return co.place_order(card_token="tok_ok")


@pytest.mark.parametrize("coupon,rate", list(COUPONS.items()))
def test_checkout_tax_applied_once_with_coupon(coupon, rate):
    """Order total must be exactly (subtotal * (1-rate)) * (1+TAX_RATE), no double-tax."""
    order = _checkout_order("SKU-002", 1, coupon)   # SKU-002 = 49.99
    raw = 49.99
    expected_total = round(round(raw * (1 - rate), 2) * (1 + TAX_RATE), 2)
    assert order.total == pytest.approx(expected_total, abs=0.01), (
        f"coupon={coupon}: expected {expected_total}, got {order.total}"
    )


def test_checkout_tax_applied_once_no_coupon():
    """Order total without coupon must be subtotal * (1 + TAX_RATE)."""
    order = _checkout_order("SKU-001", 1, None)   # SKU-001 = 19.99
    expected_total = round(19.99 * (1 + TAX_RATE), 2)
    assert order.total == pytest.approx(expected_total, abs=0.01)


def test_checkout_order_tax_field_matches_expected():
    """order.tax must be 8% of post-discount subtotal, not of original."""
    order = _checkout_order("SKU-002", 1, "SAVE20")  # 49.99, 20% off
    post_discount = round(49.99 * 0.80, 2)
    expected_tax = round(post_discount * TAX_RATE, 2)
    assert order.tax == pytest.approx(expected_tax, abs=0.01)
