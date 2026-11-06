"""Pricing rules: tax, coupons, discounts."""
from __future__ import annotations
from dataclasses import dataclass

TAX_RATE = 0.08   # 8 % sales tax

# Map coupon code -> discount fraction (0.10 = 10 % off)
COUPONS: dict[str, float] = {
    "SAVE10": 0.10,
    "SAVE20": 0.20,
    "HALFOFF": 0.50,
}


def apply_coupon(subtotal: float, code: str) -> tuple[float, float]:
    """Return (discounted_subtotal, discount_amount).

    Raises ValueError for empty, blank, or unknown coupon codes.
    """
    if not code or not code.strip():
        raise ValueError("Coupon code must not be empty")
    if code not in COUPONS:
        raise ValueError(f"Unknown coupon code: {code!r}")
    rate = COUPONS[code]
    discount = subtotal * rate
    return subtotal - discount, discount


def apply_tax(amount: float) -> float:
    """Return amount + tax."""
    return round(amount * (1 + TAX_RATE), 2)


# BUG-2 (sev2): tax is applied to the already-discounted subtotal here
# AND again inside cart.total() when build_receipt() is called — double tax.
def price_after_discount_and_tax(subtotal: float, code: str | None) -> float:
    if code:
        subtotal, _ = apply_coupon(subtotal, code)
    return apply_tax(subtotal)
