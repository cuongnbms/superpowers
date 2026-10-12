"""Web checkout."""
import calendar
import datetime as dt


def add_months(day, months):
    m = day.month - 1 + months
    year, month = day.year + m // 12, m % 12 + 1
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def create_subscription(conn, customer_id, plan, start):
    """Start a subscription bought on the web. Monthly renews in a month, annual in a year."""
    renews = add_months(start, 1 if plan == "monthly" else 12)
    cur = conn.execute(
        "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, ?, 'active', ?, 'web')",
        (customer_id, plan, renews.isoformat()),
    )
    conn.commit()
    return cur.lastrowid
