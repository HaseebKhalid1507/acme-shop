"""Regression test for acme-shop#2.

Tax must be applied exactly once — on the post-discount subtotal.
Using price_after_discount_and_tax() and then calling cart.total() (or
checkout) must not result in double taxation.
"""
import pytest
from shop.catalog import Catalog, Product
from shop.cart import Cart
from shop.checkout import Checkout
from shop.pricing import price_after_discount_and_tax, apply_tax, TAX_RATE


GROSS = 100.0
COUPON = "SAVE10"          # 10 % off → discounted subtotal = 90.0
DISCOUNTED = 90.0
EXPECTED_TAX = round(DISCOUNTED * TAX_RATE, 2)   # 7.20
EXPECTED_TOTAL = round(DISCOUNTED + EXPECTED_TAX, 2)  # 97.20


class TestIssue2PriceAfterDiscountAndTax:
    def test_returns_total_not_intermediate(self):
        """price_after_discount_and_tax must return the final total (discount + tax once)."""
        result = price_after_discount_and_tax(GROSS, COUPON)
        assert result == pytest.approx(EXPECTED_TOTAL), (
            f"Expected {EXPECTED_TOTAL}, got {result} — tax may be applied on gross or twice"
        )

    def test_no_coupon_taxes_once(self):
        """Without a coupon, price_after_discount_and_tax applies tax exactly once."""
        result = price_after_discount_and_tax(GROSS, None)
        assert result == pytest.approx(round(GROSS * (1 + TAX_RATE), 2))

    def test_result_is_not_taxable_again(self):
        """The result of price_after_discount_and_tax must already include tax.
        Applying apply_tax() on top of it would indicate double-taxing is possible."""
        result = price_after_discount_and_tax(GROSS, COUPON)
        # If result already includes tax, applying tax again gives a different (wrong) value.
        # We verify the result equals EXPECTED_TOTAL — not apply_tax(apply_tax(DISCOUNTED)).
        double_taxed = apply_tax(result)
        assert double_taxed != pytest.approx(EXPECTED_TOTAL), (
            "apply_tax applied twice still equals single-tax result — "
            "that means the first call did NOT apply tax (unexpected)"
        )
        assert result == pytest.approx(EXPECTED_TOTAL)


class TestIssue2CartTotal:
    def _make_cart(self, gross=GROSS):
        cat = Catalog([Product("P1", "Widget", gross, 10)])
        cart = Cart(cat)
        cart.add("P1", 1)
        return cart

    def test_tax_on_discounted_subtotal(self):
        """cart.total() tax must be 8% of post-discount subtotal, not of gross."""
        cart = self._make_cart()
        cart.apply_coupon(COUPON)
        result = cart.total()
        assert result["tax"] == pytest.approx(EXPECTED_TAX), (
            f"Expected tax {EXPECTED_TAX} (8% of {DISCOUNTED}), got {result['tax']}"
        )

    def test_total_equals_discounted_plus_single_tax(self):
        """cart.total() total must equal discounted_subtotal + tax (no double-tax)."""
        cart = self._make_cart()
        cart.apply_coupon(COUPON)
        result = cart.total()
        assert result["total"] == pytest.approx(EXPECTED_TOTAL), (
            f"Expected total {EXPECTED_TOTAL}, got {result['total']}"
        )

    def test_no_coupon_tax_on_gross(self):
        """Without a coupon, tax is 8% of the full subtotal."""
        cart = self._make_cart()
        result = cart.total()
        expected_tax = round(GROSS * TAX_RATE, 2)
        assert result["tax"] == pytest.approx(expected_tax)


class TestIssue2CheckoutOrder:
    def test_order_tax_on_discounted_subtotal(self):
        """Checkout order.tax must be 8% of post-discount subtotal."""
        cat = Catalog([Product("P1", "Widget", GROSS, 10)])
        cart = Cart(cat)
        cart.add("P1", 1)
        cart.apply_coupon(COUPON)
        co = Checkout(cart, cat)
        order = co.place_order(card_token="tok_ok")
        assert order.tax == pytest.approx(EXPECTED_TAX), (
            f"Expected order.tax={EXPECTED_TAX}, got {order.tax} — double-tax in checkout?"
        )
        assert order.total == pytest.approx(EXPECTED_TOTAL), (
            f"Expected order.total={EXPECTED_TOTAL}, got {order.total}"
        )

    def test_order_total_consistent_with_breakdown(self):
        """order.total must equal order.subtotal - order.discount + order.tax."""
        cat = Catalog([Product("P1", "Widget", GROSS, 10)])
        cart = Cart(cat)
        cart.add("P1", 1)
        cart.apply_coupon(COUPON)
        co = Checkout(cart, cat)
        order = co.place_order(card_token="tok_ok")
        recomputed = round(order.subtotal - order.discount + order.tax, 2)
        assert order.total == pytest.approx(recomputed), (
            f"Order total {order.total} != subtotal-discount+tax {recomputed}"
        )
