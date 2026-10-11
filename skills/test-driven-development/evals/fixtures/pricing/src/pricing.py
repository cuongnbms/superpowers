def cart_total(items):
    """Total price of a cart in cents."""
    return sum(item["price_cents"] * item["qty"] for item in items)
