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
        """Return a breakdown dict: subtotal, discount, tax, total."""
        subtotal = self.raw_subtotal()
        discount = 0.0

        if self._coupon is not None:
            # BUG-1 trigger: empty string crashes here with KeyError
            discounted, discount = apply_coupon(subtotal, self._coupon)
            subtotal = discounted

        tax = round(subtotal * TAX_RATE, 2)
        # BUG-2: if price_after_discount_and_tax() was also called externally
        # (e.g. from a preview endpoint), tax gets applied a second time on
        # receipt generation because apply_tax() is called again below.
        total = round(subtotal + tax, 2)

        return {
            "subtotal": self.raw_subtotal(),
            "discount": round(discount, 2),
            "tax": tax,
            "total": total,
            "coupon": self._coupon,
        }
