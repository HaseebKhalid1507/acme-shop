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


# BUG-2 fix: removed the apply_tax() call from this helper.
# The old implementation applied tax inside the function AND callers
# (Cart.total, checkout receipt) also called apply_tax on the result,
# charging customers tax twice on coupon orders.
# This function now returns only the post-discount subtotal; callers
# are responsible for applying tax via apply_tax().
def price_after_discount_and_tax(subtotal: float, code: str | None) -> float:
    """Return post-discount subtotal (without tax).

    Callers that need the final with-tax total should follow up with
    ``apply_tax(price_after_discount_and_tax(subtotal, code))``.
    """
    if code:
        subtotal, _ = apply_coupon(subtotal, code)
    return subtotal
