"""Regression test for acme-shop#2: tax applied twice on orders with discount coupon.

Root causes found in gen-2:
1. price_after_discount_and_tax() and cart.total() computed the final total via
   different rounding paths, so a customer's preview price could differ from what
   they were actually charged — a financial integrity violation.
2. Structural risk of double-tax: both functions applied tax independently;
   chaining them would tax the customer twice.

Fix: cart.total() delegates to price_after_discount_and_tax() so there is
exactly one tax computation path.
"""
import pytest
from shop.pricing import apply_coupon, apply_tax, price_after_discount_and_tax, TAX_RATE
from shop.catalog import Catalog, Product
from shop.cart import Cart
from shop.checkout import Checkout


# ---------------------------------------------------------------------------
# price_after_discount_and_tax: single tax application
# ---------------------------------------------------------------------------

def test_price_after_discount_no_double_tax():
    """The result of price_after_discount_and_tax() must NOT equal apply_tax() on itself."""
    gross = 100.0
    already_taxed = price_after_discount_and_tax(gross, "SAVE10")  # 97.20
    would_be_double = apply_tax(already_taxed)                     # 104.976
    assert would_be_double != pytest.approx(already_taxed)


# ---------------------------------------------------------------------------
# cart.total() must agree with price_after_discount_and_tax() — exact match,
# same rounding — so the preview price equals the charge.
# ---------------------------------------------------------------------------

# Amounts and codes that reveal the rounding discrepancy in the unfixed code.
ROUNDING_CASES = [
    (29.95, "HALFOFF"),    # method1=16.17, method2=16.18 (unfixed)
    (33.33, "SAVE20"),     # method1=28.80, method2=28.79
    (33.33, "HALFOFF"),    # method1=18.00, method2=17.99
    (49.99, "HALFOFF"),    # method1=26.99, method2=27.00
    (77.77, "SAVE20"),     # method1=67.19, method2=67.20
    (123.45, "SAVE10"),    # method1=119.99, method2=120.00
]


@pytest.mark.parametrize("unit_price,code", ROUNDING_CASES)
def test_cart_total_matches_preview(unit_price, code):
    """cart.total()['total'] must exactly equal price_after_discount_and_tax().

    A mismatch means the customer is shown one price but charged another.
    """
    catalog = Catalog([Product("X1", "Test", unit_price, 100)])
    cart = Cart(catalog)
    cart.add("X1", 1)
    cart.apply_coupon(code)

    t = cart.total()
    expected = price_after_discount_and_tax(unit_price, code)
    assert t["total"] == pytest.approx(expected), (
        f"Preview price ({expected}) differs from charged total ({t['total']}) "
        f"for {unit_price=} {code=} — customer would be over/undercharged"
    )


def test_cart_total_tax_on_post_discount():
    """Tax in cart.total() must be on the post-discount amount, not on the gross."""
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-002", 1)        # 49.99
    cart.apply_coupon("SAVE20")
    t = cart.total()

    # Gross tax would be 49.99 * 0.08 = 4.00; post-discount tax should be less
    gross_tax = round(t["subtotal"] * TAX_RATE, 2)
    assert t["tax"] < gross_tax, (
        f"Tax {t['tax']} should be less than gross tax {gross_tax}"
    )


def test_cart_total_no_coupon_unchanged():
    """Without a coupon, total must still be subtotal * 1.08 (single tax)."""
    catalog = Catalog.default()
    cart = Cart(catalog)
    cart.add("SKU-003", 3)   # 3 × 9.99 = 29.97
    t = cart.total()
    assert t["discount"] == 0.0
    assert t["total"] == pytest.approx(apply_tax(t["subtotal"]))


# ---------------------------------------------------------------------------
# End-to-end: order total must match the preview price exactly
# ---------------------------------------------------------------------------

def test_checkout_total_matches_preview():
    """The order total placed via Checkout must equal the cart preview total."""
    catalog = Catalog([Product("X2", "PriceItem", 29.95, 100)])
    cart = Cart(catalog)
    cart.add("X2", 1)
    cart.apply_coupon("HALFOFF")

    preview = cart.total()["total"]   # what the customer sees
    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")

    assert order.total == pytest.approx(preview), (
        f"Customer shown {preview} but charged {order.total}"
    )


def test_checkout_order_total_uses_price_after_discount_and_tax():
    """Order total must equal price_after_discount_and_tax(gross, code) — the canonical formula."""
    catalog = Catalog([Product("X3", "BigItem", 33.33, 100)])
    cart = Cart(catalog)
    cart.add("X3", 1)
    cart.apply_coupon("SAVE20")

    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")

    expected_total = price_after_discount_and_tax(33.33, "SAVE20")
    assert order.total == pytest.approx(expected_total)
    # Confirm NOT the wrong (double-tax) value
    assert order.total != pytest.approx(apply_tax(expected_total))
