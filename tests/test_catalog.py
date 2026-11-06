"""Tests for catalog — all pass on main."""
import pytest
from shop.catalog import Catalog, Product


def test_default_catalog_has_products():
    c = Catalog.default()
    assert len(c.all()) == 5


def test_get_known_product():
    c = Catalog.default()
    p = c.get("SKU-001")
    assert p is not None
    assert p.name == "Widget Pro"
    assert p.price == 19.99


def test_get_unknown_returns_none():
    c = Catalog.default()
    assert c.get("NOPE") is None


def test_search_by_name():
    c = Catalog.default()
    results = c.search("widget")
    assert any(p.id == "SKU-001" for p in results)


def test_search_by_category():
    c = Catalog.default()
    results = c.search("misc")
    ids = {p.id for p in results}
    assert "SKU-003" in ids and "SKU-005" in ids


def test_adjust_stock():
    c = Catalog.default()
    p = c.get("SKU-001")
    original = p.stock
    c.adjust_stock("SKU-001", -5)
    assert c.get("SKU-001").stock == original - 5


def test_product_round_trip():
    p = Product("X1", "Test", 9.99, 10, "cat", ["a", "b"])
    assert Product.from_dict(p.to_dict()) == p
