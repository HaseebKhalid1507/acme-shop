"""Tests for checkout — all pass on main (bug-3 not triggered)."""
import pytest
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout, PaymentError


@pytest.fixture
def setup():
    catalog = Catalog.default()
    cart = Cart(catalog)
    return catalog, cart


def test_successful_checkout(setup):
    catalog, cart = setup
    cart.add("SKU-003")   # cheapest item
    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")
    assert order.status == "paid"
    assert order.total > 0


def test_checkout_empties_cart(setup):
    catalog, cart = setup
    cart.add("SKU-003")
    co = Checkout(cart, catalog)
    co.place_order(card_token="tok_ok")
    assert len(cart.items) == 0


def test_payment_failure_raises(setup):
    catalog, cart = setup
    cart.add("SKU-003")
    co = Checkout(cart, catalog)
    with pytest.raises(PaymentError):
        co.place_order(card_token="FAIL")


def test_empty_cart_raises(setup):
    catalog, cart = setup
    co = Checkout(cart, catalog)
    with pytest.raises(ValueError, match="empty cart"):
        co.place_order()


def test_order_stored(setup):
    catalog, cart = setup
    cart.add("SKU-001")
    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")
    assert Checkout.get_order(order.order_id) is not None


def test_order_items_correct(setup):
    catalog, cart = setup
    cart.add("SKU-001", 2)
    co = Checkout(cart, catalog)
    order = co.place_order(card_token="tok_ok")
    assert len(order.items) == 1
    assert order.items[0]["qty"] == 2
