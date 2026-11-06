"""Checkout: inventory reservation, payment stub, order finalization."""
from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional
from shop.cart import Cart
from shop.catalog import Catalog
from shop.pricing import apply_tax


@dataclass
class Order:
    order_id: str
    items: list[dict]      # [{product_id, name, qty, unit_price, subtotal}]
    subtotal: float
    discount: float
    tax: float
    total: float
    coupon: Optional[str]
    payment_method: str
    status: str            # "pending" | "paid" | "failed"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class PaymentError(Exception):
    pass


def _stub_payment(method: str, amount: float, card_token: str | None) -> str:
    """Pretend to charge.  Returns transaction_id.  Raise PaymentError to simulate failure."""
    if card_token == "FAIL":
        raise PaymentError("Card declined (stub)")
    return f"txn-{uuid.uuid4().hex[:8]}"


class Checkout:
    """Single-use checkout session for one cart."""

    # Keeps a simple in-memory order store (good enough for a demo / tests)
    _orders: dict[str, Order] = {}

    def __init__(self, cart: Cart, catalog: Catalog):
        self._cart = cart
        self._catalog = catalog
        self._reserved: dict[str, int] = {}   # product_id -> qty reserved

    def _reserve(self) -> None:
        """Decrement stock for all items in the cart."""
        for li in self._cart.items:
            self._catalog.adjust_stock(li.product.id, -li.qty)
            self._reserved[li.product.id] = li.qty

    def _release(self) -> None:
        """Return reserved stock on payment failure.

        BUG-3 (sev2): this method is never called on PaymentError — stock
        stays decremented even when payment fails, leaking inventory.
        """
        # the loop is correct but _release() is not called in place_order()
        for pid, qty in self._reserved.items():
            self._catalog.adjust_stock(pid, qty)
        self._reserved.clear()

    def place_order(
        self,
        payment_method: str = "card",
        card_token: str | None = None,
    ) -> Order:
        if not self._cart.items:
            raise ValueError("Cannot check out an empty cart")

        breakdown = self._cart.total()
        self._reserve()

        try:
            _stub_payment(payment_method, breakdown["total"], card_token)
        except PaymentError:
            # BUG-3: should call self._release() here — intentionally omitted
            raise

        order = Order(
            order_id=f"ORD-{uuid.uuid4().hex[:6].upper()}",
            items=[
                {
                    "product_id": li.product.id,
                    "name": li.product.name,
                    "qty": li.qty,
                    "unit_price": li.product.price,
                    "subtotal": li.subtotal,
                }
                for li in self._cart.items
            ],
            subtotal=breakdown["subtotal"],
            discount=breakdown["discount"],
            tax=breakdown["tax"],
            total=breakdown["total"],
            coupon=breakdown["coupon"],
            payment_method=payment_method,
            status="paid",
        )
        Checkout._orders[order.order_id] = order
        self._cart.clear()
        return order

    @classmethod
    def get_order(cls, order_id: str) -> Optional[Order]:
        return cls._orders.get(order_id)
