import datetime as dt

from app.billing import add_months, create_subscription
from tests.helpers import add_customer, fresh_db


def test_add_months_clamps_to_month_end():
    assert add_months(dt.date(2026, 1, 31), 1) == dt.date(2026, 2, 28)


def test_web_annual_subscription_renews_in_a_year():
    conn = fresh_db()
    add_customer(conn, 7)
    sid = create_subscription(conn, 7, "annual", dt.date(2026, 3, 4))
    assert conn.execute("SELECT plan, status, renews_at FROM subscriptions WHERE id = ?", (sid,)).fetchone() == (
        "annual", "active", "2027-03-04")
