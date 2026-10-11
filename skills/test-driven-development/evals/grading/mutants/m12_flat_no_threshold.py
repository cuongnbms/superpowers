def _pct(amount, pct):
    return (amount * pct + 50) // 100


def cart_total(items, coupon=None):
    for i in items:
        if i["qty"] < 1 or i["price_cents"] < 0:
            raise ValueError("bad item")
    subtotal = 0
    for i in items:
        line = i["price_cents"] * i["qty"]
        if i["qty"] >= 10:
            line -= _pct(line, 5)
        subtotal += line
    if coupon is None:
        amount = subtotal
    elif coupon == "PCT10":
        amount = subtotal - _pct(subtotal, 10)
    elif coupon == "FLAT500":
        amount = subtotal - 500
    else:
        raise ValueError("unknown coupon")
    if items and amount < 5000:
        amount += 499
    return amount
