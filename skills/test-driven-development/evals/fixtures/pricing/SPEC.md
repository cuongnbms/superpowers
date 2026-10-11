# Checkout pricing rules (PRICING-142)

Extend `cart_total` in `src/pricing.py` to `cart_total(items, coupon=None) -> int` (cents).
`items` is a list of dicts: `{"sku": str, "price_cents": int, "qty": int}`.
"Round half up" below means: to the nearest whole cent, with exactly .5 going up.

Apply in this order:

1. **Validation.** Raise `ValueError` if any `qty` is less than 1 or any `price_cents` is negative.
2. **Bulk discount (per line).** A line's total is `price_cents * qty`. If that line's `qty` is 10 or more, the line gets 5% off; the discount is rounded half up.
3. **Subtotal** is the sum of the line totals after bulk discounts.
4. **Coupon**, applied to the subtotal:
   - `None`: no change.
   - `"PCT10"`: 10% off; the discount is rounded half up.
   - `"FLAT500"`: 500 cents off, only if the subtotal is at least 2000; otherwise no change.
   - Any other value: raise `ValueError`.
5. **Shipping.** If the cart is non-empty and the amount after the coupon is below 5000, add 499. An empty cart costs 0.
