"""Regression test for acme-shop#3.

Inventory must be released (stock restored) when payment fails.
Before the fix, _release() was never called on PaymentError, so stock stayed
decremented permanently — causing inventory to drift negative.
"""
import pytest
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout, PaymentError


@pytest.fixture
def setup():
    catalog = Catalog.default()
    cart = Cart(catalog)
    return catalog, cart


def test_stock_restored_after_payment_failure(setup):
    """Stock must return to its pre-checkout level when payment is declined."""
    catalog, cart = setup
    stock_before = catalog.get("SKU-004").stock  # 10

    cart.add("SKU-004", qty=3)
    co = Checkout(cart, catalog)
    with pytest.raises(PaymentError):
        co.place_order(card_token="FAIL")

    stock_after = catalog.get("SKU-004").stock
    assert stock_after == stock_before, (
        f"Expected stock {stock_before} after failed payment, got {stock_after}. "
        "Inventory was not released."
    )


def test_stock_decremented_after_successful_order(setup):
    """Control: stock IS reduced on a successful order."""
    catalog, cart = setup
    cart.add("SKU-004", qty=2)

    co = Checkout(cart, catalog)
    co.place_order(card_token=None)

    assert catalog.get("SKU-004").stock == 8
