"""Regression test for acme-shop#2.

Tax must be applied exactly once, on the post-discount subtotal.
Before the fix, price_after_discount_and_tax() applied tax internally,
so any caller that used it as a subtotal and then also called cart.total()
(or any path that re-applied tax) would double-charge the customer.
"""
import pytest
from shop.pricing import price_after_discount_and_tax, apply_coupon, apply_tax, TAX_RATE
from shop.cart import Cart
from shop.catalog import Catalog
from shop.checkout import Checkout


# ---------------------------------------------------------------------------
# price_after_discount_and_tax — must NOT include tax (it's a subtotal helper)
# ---------------------------------------------------------------------------

def test_price_after_discount_and_tax_no_coupon_excludes_tax():
    """Without a coupon, price_after_discount_and_tax should return the raw
    subtotal (no tax baked in) so callers can apply tax exactly once."""
    result = price_after_discount_and_tax(100.0, None)
    assert result == pytest.approx(100.0), (
        "price_after_discount_and_tax should return post-discount subtotal, "
        "not post-discount+tax"
    )


def test_price_after_discount_and_tax_with_coupon_excludes_tax():
    """With a coupon, price_after_discount_and_tax should return only the
    discounted subtotal — tax must NOT be baked in."""
    discounted, _ = apply_coupon(100.0, "SAVE10")   # 90.0
    result = price_after_discount_and_tax(100.0, "SAVE10")
    assert result == pytest.approx(discounted), (
        "price_after_discount_and_tax should return 90.0 (post-discount), "
        f"not {apply_tax(discounted)} (post-discount+tax)"
    )


# ---------------------------------------------------------------------------
# cart.total() — tax must be on discounted subtotal, applied exactly once
# ---------------------------------------------------------------------------

@pytest.fixture
def cart_with_coupon():
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-001", 5)   # 5 × $19.99 = $99.95
    cart.apply_coupon("SAVE10")
    return cart


def test_cart_total_tax_on_discounted_subtotal(cart_with_coupon):
    """Tax must be computed on the post-discount subtotal, not the raw subtotal."""
    t = cart_with_coupon.total()
    raw = t["subtotal"]          # 99.95
    discount = t["discount"]     # ~10.0
    discounted = raw - discount  # ~89.95
    expected_tax = round(discounted * TAX_RATE, 2)
    assert t["tax"] == pytest.approx(expected_tax, abs=0.01), (
        f"Tax {t['tax']} should be ~{expected_tax} (8% of discounted {discounted}), "
        f"not {round(raw * TAX_RATE, 2)} (8% of raw {raw})"
    )


def test_cart_total_no_double_tax_with_coupon(cart_with_coupon):
    """cart.total() must not apply tax twice when a coupon is active."""
    t = cart_with_coupon.total()
    raw = t["subtotal"]
    discount = t["discount"]
    discounted = raw - discount
    # Single-tax total
    expected_tax = round(discounted * TAX_RATE, 2)
    expected_total = round(discounted + expected_tax, 2)
    assert t["total"] == pytest.approx(expected_total, abs=0.01), (
        f"total {t['total']} differs from expected {expected_total}; "
        "possible double-tax"
    )


def test_cart_total_consistent_with_price_after_discount_and_tax(cart_with_coupon):
    """cart.total() and price_after_discount_and_tax must agree on the
    post-discount subtotal (before tax)."""
    t = cart_with_coupon.total()
    raw = t["subtotal"]                                   # 99.95
    post_discount = price_after_discount_and_tax(raw, "SAVE10")  # must be 89.955
    # post_discount + tax should equal cart total
    tax = round(post_discount * TAX_RATE, 2)
    expected_total = round(post_discount + tax, 2)
    assert t["total"] == pytest.approx(expected_total, abs=0.01)


# ---------------------------------------------------------------------------
# checkout order — tax in the final order must match cart.total() tax
# ---------------------------------------------------------------------------

def test_checkout_order_tax_matches_cart_total():
    """The tax recorded on the order must equal what cart.total() computed —
    no second application of tax during place_order()."""
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-002", 2)   # 2 × $49.99 = $99.98
    cart.apply_coupon("SAVE20")
    expected = cart.total()

    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")

    assert order.tax == pytest.approx(expected["tax"], abs=0.01)
    assert order.total == pytest.approx(expected["total"], abs=0.01)


def test_checkout_order_tax_is_single_rate_on_discounted_amount():
    """Tax on the final order must be exactly TAX_RATE × post-discount subtotal."""
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-002", 2)   # 2 × $49.99 = $99.98
    cart.apply_coupon("SAVE20")
    raw_subtotal = cart.raw_subtotal()          # 99.98
    discount_rate = 0.20
    discounted = round(raw_subtotal * (1 - discount_rate), 2)  # ~79.98

    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")

    expected_tax = round(discounted * TAX_RATE, 2)
    assert order.tax == pytest.approx(expected_tax, abs=0.02), (
        f"Order tax {order.tax} != expected {expected_tax} "
        f"(single TAX_RATE on discounted {discounted})"
    )
