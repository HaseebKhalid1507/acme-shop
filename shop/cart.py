"""Shopping cart: add/remove items, apply coupons, compute totals."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from shop.catalog import Catalog, Product
from shop.pricing import COUPONS, apply_coupon, apply_tax, TAX_RATE


@dataclass
class LineItem:
    product: Product
    qty: int

    @property
    def subtotal(self) -> float:
        return round(self.product.price * self.qty, 2)


class Cart:
    def __init__(self, catalog: Catalog):
        self._catalog = catalog
        self._items: dict[str, LineItem] = {}   # product_id -> LineItem
        self._coupon: Optional[str] = None

    # ------------------------------------------------------------------ #
    def add(self, product_id: str, qty: int = 1) -> None:
        p = self._catalog.get(product_id)
        if p is None:
            raise ValueError(f"Unknown product: {product_id}")
        if qty < 1:
            raise ValueError("qty must be >= 1")
        if p.stock < qty:
            raise ValueError(f"Insufficient stock for {product_id}")
        if product_id in self._items:
            self._items[product_id].qty += qty
        else:
            self._items[product_id] = LineItem(product=p, qty=qty)

    def remove(self, product_id: str) -> None:
        self._items.pop(product_id, None)

    def set_qty(self, product_id: str, qty: int) -> None:
        if qty <= 0:
            self.remove(product_id)
            return
        if product_id not in self._items:
            raise ValueError(f"{product_id} not in cart")
        self._items[product_id].qty = qty

    def apply_coupon(self, code: str) -> None:
        """Set the active coupon.  Validation happens at total() time."""
        self._coupon = code

    def clear(self) -> None:
        self._items.clear()
        self._coupon = None

    # ------------------------------------------------------------------ #
    @property
    def items(self) -> list[LineItem]:
        return list(self._items.values())

    def raw_subtotal(self) -> float:
        return round(sum(li.subtotal for li in self._items.values()), 2)

    def total(self) -> dict:
        """Return a breakdown dict: original_subtotal, subtotal, discount, tax, total.

        ``subtotal`` is the post-discount pre-tax amount (the tax base), so that
        ``subtotal + tax == total`` always holds.
        ``original_subtotal`` is the raw pre-discount amount kept for display.
        """
        original_subtotal = self.raw_subtotal()
        subtotal = original_subtotal
        discount = 0.0

        if self._coupon is not None:
            subtotal, discount = apply_coupon(subtotal, self._coupon)

        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax, 2)

        return {
            "original_subtotal": original_subtotal,
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "tax": tax,
            "total": total,
            "coupon": self._coupon,
        }
