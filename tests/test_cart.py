"""Tests for cart — all pass on main (bugs are not exercised here)."""
import pytest
from shop.catalog import Catalog
from shop.cart import Cart


@pytest.fixture
def cart():
    return Cart(Catalog.default())


def test_add_item(cart):
    cart.add("SKU-001", 2)
    assert len(cart.items) == 1
    assert cart.items[0].qty == 2


def test_add_increases_qty(cart):
    cart.add("SKU-001", 1)
    cart.add("SKU-001", 2)
    assert cart.items[0].qty == 3


def test_remove_item(cart):
    cart.add("SKU-001")
    cart.remove("SKU-001")
    assert len(cart.items) == 0


def test_raw_subtotal(cart):
    cart.add("SKU-001", 2)   # 2 * 19.99 = 39.98
    assert cart.raw_subtotal() == 39.98


def test_total_no_coupon(cart):
    cart.add("SKU-003")   # 9.99
    t = cart.total()
    assert t["discount"] == 0.0
    assert t["subtotal"] == 9.99
    assert round(t["tax"], 2) == round(9.99 * 0.08, 2)
    assert t["total"] == round(9.99 * 1.08, 2)


def test_valid_coupon_applies(cart):
    cart.add("SKU-002")   # 49.99
    cart.apply_coupon("SAVE10")
    t = cart.total()
    assert t["discount"] == round(49.99 * 0.10, 2)
    assert t["total"] < 49.99 * 1.08


def test_unknown_product_raises(cart):
    with pytest.raises(ValueError, match="Unknown product"):
        cart.add("FAKE")


def test_zero_qty_raises(cart):
    with pytest.raises(ValueError):
        cart.add("SKU-001", 0)


def test_set_qty(cart):
    cart.add("SKU-001", 3)
    cart.set_qty("SKU-001", 1)
    assert cart.items[0].qty == 1


def test_set_qty_zero_removes(cart):
    cart.add("SKU-001", 3)
    cart.set_qty("SKU-001", 0)
    assert len(cart.items) == 0


def test_clear(cart):
    cart.add("SKU-001")
    cart.add("SKU-002")
    cart.clear()
    assert len(cart.items) == 0
    assert cart._coupon is None
