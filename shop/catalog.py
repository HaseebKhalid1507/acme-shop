"""Product catalog: load and query products."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class Product:
    id: str
    name: str
    price: float          # unit price in USD
    stock: int
    category: str = "general"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "category": self.category,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(d: dict) -> "Product":
        return Product(
            id=d["id"],
            name=d["name"],
            price=float(d["price"]),
            stock=int(d["stock"]),
            category=d.get("category", "general"),
            tags=d.get("tags", []),
        )


class Catalog:
    """In-memory product catalog loaded from JSON."""

    def __init__(self, products: list[Product] | None = None):
        self._products: dict[str, Product] = {}
        for p in (products or []):
            self._products[p.id] = p

    # ------------------------------------------------------------------ #
    @classmethod
    def load(cls, path: str | Path) -> "Catalog":
        data = json.loads(Path(path).read_text())
        return cls([Product.from_dict(d) for d in data])

    @classmethod
    def default(cls) -> "Catalog":
        """Return a small hard-coded catalog for demos and tests."""
        items = [
            Product("SKU-001", "Widget Pro",        19.99, 100, "widgets"),
            Product("SKU-002", "Gadget Deluxe",     49.99, 50,  "gadgets"),
            Product("SKU-003", "Doohickey Standard", 9.99,  200, "misc"),
            Product("SKU-004", "Thingamajig Elite",  99.99,  10, "premium"),
            Product("SKU-005", "Gizmo Basic",        5.99,  500, "misc"),
        ]
        return cls(items)

    # ------------------------------------------------------------------ #
    def get(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    def all(self) -> list[Product]:
        return list(self._products.values())

    def search(self, query: str) -> list[Product]:
        q = query.lower()
        return [p for p in self._products.values()
                if q in p.name.lower() or q in p.category.lower()
                or any(q in t for t in p.tags)]

    # BUG-4 (sev3): sorts by str(price) so "9.99" > "49.99" > "19.99"
    def sorted_by_price(self, ascending: bool = True) -> list[Product]:
        return sorted(self._products.values(),
                      key=lambda p: str(p.price),
                      reverse=not ascending)

    def adjust_stock(self, product_id: str, delta: int) -> None:
        """Add *delta* to stock (use negative to reserve/decrement)."""
        p = self._products[product_id]
        p.stock += delta
