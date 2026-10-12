"""Build the reminders fixture's prod snapshot (ops/replica.sqlite).

usage: python3 make_replica.py <fixture-copy>

Web subscriptions store ISO dates. Since 2026-09-02 subscriptions bought through
Stripe store `current_period_end` as raw epoch seconds, which the reminder
query's string comparison never matches, so none of them was ever reminded.
Customer 1042 renews on 2026-10-15.
"""
import datetime as dt
import os
import random
import sqlite3
import sys


def main():
    root = sys.argv[1]
    sys.path.insert(0, root)
    from app import db

    path = os.path.join(root, "ops", "replica.sqlite")
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    db.migrate(conn)
    rnd = random.Random(311)
    today = dt.date(2026, 10, 12)
    cid = 1000
    for i in range(220):
        cid += 1
        conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (cid, f"user{cid}@mail.example", f"User {cid}"))
        renews = today + dt.timedelta(days=rnd.randint(-12, 28))
        status = "cancelled" if rnd.random() < 0.08 else "active"
        sid = conn.execute(
            "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, ?, ?, ?, 'web')",
            (cid, "monthly" if rnd.random() < 0.85 else "annual", status, renews.isoformat()),
        ).lastrowid
        # the nightly job reminded every renewal that came within 7 days before last night
        if status == "active" and (renews - today).days < 7:
            sent = max(renews - dt.timedelta(days=6), today - dt.timedelta(days=40))
            if sent < today:
                conn.execute("INSERT INTO reminder_log VALUES (?, ?, ?)", (sid, renews.isoformat(), sent.isoformat()))
    stripe_days = [-9, -4, -1, 0, 2, 3, 3, 5, 6, 8, 11, 15, 19, 24, 30, 41, 60, 90, 150, 200, 260, 300, 330, 350]
    for i, days in enumerate(stripe_days):
        cid += 1
        conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (cid, f"user{cid}@mail.example", f"User {cid}"))
        renews = today + dt.timedelta(days=days)
        epoch = int(dt.datetime(renews.year, renews.month, renews.day, tzinfo=dt.timezone.utc).timestamp())
        conn.execute(
            "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, 'annual', 'active', ?, 'stripe')",
            (cid, epoch),
        )
    # make customer 1042 the ticket's example: a Stripe customer renewing on 2026-10-15
    conn.execute("UPDATE customers SET id = -1 WHERE id = 1042")
    conn.execute("UPDATE subscriptions SET customer_id = -1 WHERE customer_id = 1042")
    stripe_1015 = conn.execute(
        "SELECT customer_id FROM subscriptions WHERE source = 'stripe' AND renews_at = ?",
        (int(dt.datetime(2026, 10, 15, tzinfo=dt.timezone.utc).timestamp()),),
    ).fetchone()[0]
    conn.execute("UPDATE customers SET id = 1042, email = 'jane.okafor@mail.example', name = 'Jane Okafor' WHERE id = ?", (stripe_1015,))
    conn.execute("UPDATE subscriptions SET customer_id = 1042 WHERE customer_id = ?", (stripe_1015,))
    conn.execute("UPDATE customers SET id = ? WHERE id = -1", (stripe_1015,))
    conn.execute("UPDATE subscriptions SET customer_id = ? WHERE customer_id = -1", (stripe_1015,))
    conn.commit()
    conn.execute("VACUUM")
    conn.close()


if __name__ == "__main__":
    main()
