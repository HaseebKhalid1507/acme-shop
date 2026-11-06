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

    Raises ValueError for an empty or unrecognised coupon code.
    """
    if not code or code not in COUPONS:
        raise ValueError(f"Invalid coupon code: {code!r}")
    rate = COUPONS[code]
    discount = subtotal * rate
    return subtotal - discount, discount


def apply_tax(amount: float) -> float:
    """Return amount + tax."""
    return round(amount * (1 + TAX_RATE), 2)


# BUG-2 fix: removed apply_tax() from this helper so it returns only the
# post-discount subtotal. Tax is applied exactly once by the caller (cart.total()).
def price_after_discount_and_tax(subtotal: float, code: str | None) -> float:
    """Return the post-discount subtotal (tax NOT included).

    Tax is applied exactly once by cart.total() / the caller.  This function
    must NOT call apply_tax() so that callers that subsequently compute
    ``subtotal * TAX_RATE`` do not double-charge the customer.
    """
    if code:
        subtotal, _ = apply_coupon(subtotal, code)
    return subtotal
