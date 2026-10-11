import pytest
from src.pricing import cart_total


def it(price, qty, sku="A"):
    return {"sku": sku, "price_cents": price, "qty": qty}


@pytest.mark.parametrize("items,coupon,expected", [
    ([it(3000, 1), it(1500, 2, "B")], None, 6000),
    ([it(1000, 1)], None, 1499),
    ([], None, 0),
    ([it(5000, 1)], None, 5000),
    ([it(100, 10)], None, 1449),
    ([it(101, 10)], None, 1458),
    ([it(2000, 1)], "FLAT500", 1999),
    ([it(1999, 1)], "FLAT500", 2498),
    ([it(5200, 1)], "FLAT500", 5199),
    ([it(1000, 10)], "PCT10", 8550),
    ([it(100, 5), it(100, 5, "B")], None, 1499),
    ([it(6005, 1)], "PCT10", 5404),
])
def test_totals(items, coupon, expected):
    assert cart_total(items, coupon) == expected


@pytest.mark.parametrize("items,coupon", [
    ([it(1000, 1)], "BOGUS"),
    ([it(1000, 0)], None),
    ([it(-1, 1)], None),
])
def test_rejects(items, coupon):
    with pytest.raises(ValueError):
        cart_total(items, coupon)
