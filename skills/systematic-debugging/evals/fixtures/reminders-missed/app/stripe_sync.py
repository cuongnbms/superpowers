"""Stripe webhooks: keep subscriptions bought through Stripe in sync."""


def handle_subscription_updated(conn, event):
    """Apply a customer.subscription.created / .updated event."""
    obj = event["data"]["object"]
    customer_id = int(obj["metadata"]["customer_id"])
    plan = "annual" if obj["plan"]["interval"] == "year" else "monthly"
    status = "active" if obj["status"] in ("active", "trialing") else "cancelled"
    renews_at = obj["current_period_end"]
    row = conn.execute(
        "SELECT id FROM subscriptions WHERE customer_id = ? AND source = 'stripe'", (customer_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE subscriptions SET plan = ?, status = ?, renews_at = ? WHERE id = ?",
            (plan, status, renews_at, row[0]),
        )
        sub_id = row[0]
    else:
        sub_id = conn.execute(
            "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, ?, ?, ?, 'stripe')",
            (customer_id, plan, status, renews_at),
        ).lastrowid
    conn.commit()
    return sub_id
