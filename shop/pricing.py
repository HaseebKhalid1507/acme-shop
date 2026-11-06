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

    BUG-1 (sev1): empty string '' is not in COUPONS but the lookup
    falls through to returning (subtotal - subtotal * None) which raises
    TypeError — manifests as a crash / NaN in callers that don't guard.
    Actually implemented: empty code is treated as valid → KeyError
    propagates to cart.total(), crashing the whole request.
    """
    if not code or code not in COUPONS:
        raise ValueError(f"Invalid coupon code: {code!r}")
    rate = COUPONS[code]
    discount = subtotal * rate
    return subtotal - discount, discount


def apply_tax(amount: float) -> float:
    """Return amount + tax."""
    return round(amount * (1 + TAX_RATE), 2)


# BUG-2 fix: removed the apply_tax() call here.  Tax is computed exactly once
# inside cart.total() (and therefore in Checkout.place_order).  This helper
# now returns only the post-discount subtotal so any caller that subsequently
# passes the value through cart.total() / checkout does not double-tax.
def price_after_discount_and_tax(subtotal: float, code: str | None) -> float:
    if code:
        subtotal, _ = apply_coupon(subtotal, code)
    return subtotal
