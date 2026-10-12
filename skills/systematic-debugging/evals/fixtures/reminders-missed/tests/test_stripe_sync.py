from app.stripe_sync import handle_subscription_updated
from tests.helpers import add_customer, fresh_db


def event(customer_id, interval="year", status="active", period_end=1792022400):
    return {"type": "customer.subscription.updated", "data": {"object": {
        "metadata": {"customer_id": str(customer_id)},
        "plan": {"interval": interval},
        "status": status,
        "current_period_end": period_end,
    }}}


def test_creates_annual_subscription():
    conn = fresh_db()
    add_customer(conn, 9)
    sid = handle_subscription_updated(conn, event(9))
    assert conn.execute("SELECT plan, status, source FROM subscriptions WHERE id = ?", (sid,)).fetchone() == (
        "annual", "active", "stripe")


def test_cancellation_updates_the_same_row():
    conn = fresh_db()
    add_customer(conn, 9)
    first = handle_subscription_updated(conn, event(9))
    second = handle_subscription_updated(conn, event(9, status="canceled"))
    assert first == second
    assert conn.execute("SELECT status FROM subscriptions WHERE id = ?", (first,)).fetchone() == ("cancelled",)
