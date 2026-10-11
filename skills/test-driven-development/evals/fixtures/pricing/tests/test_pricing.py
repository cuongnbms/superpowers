from src.pricing import cart_total


def test_sums_lines():
    items = [{"sku": "A", "price_cents": 3000, "qty": 1}, {"sku": "B", "price_cents": 1500, "qty": 2}]
    assert cart_total(items) == 6000
