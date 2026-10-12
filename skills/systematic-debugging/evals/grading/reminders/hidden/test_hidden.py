"""Acceptance tests for the reminders case, run against a run's app/ and migrations/.

A fix may convert at write time and migrate existing rows, or read both formats;
either passes.
"""
import datetime as dt
import os
import sqlite3

from app import db
from app.reminders import due_reminders, send_due
from app.stripe_sync import handle_subscription_updated

TODAY = dt.date(2026, 10, 12)
OCT15 = 1792022400  # 2026-10-15T00:00:00Z


def epoch(day):
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())


def prod_like_db():
    """A database at the schema prod had before the fix, with an existing Stripe row."""
    conn = sqlite3.connect(":memory:")
    with open(os.path.join(db.MIGRATIONS, "001_init.sql")) as f:
        conn.executescript(f.read())
    conn.execute("CREATE TABLE schema_migrations (name TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO schema_migrations VALUES ('001_init.sql')")
    for cid in (1, 2, 3, 4, 5, 6):
        conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (cid, f"c{cid}@x", f"C{cid}"))
    rows = [
        (1, "annual", "active", str(OCT15), "stripe"),                       # existing Stripe row
        (2, "monthly", "active", "2026-10-18", "web"),                       # 6 days: due
        (3, "monthly", "active", "2026-10-19", "web"),                       # 7 days: not yet
        (4, "annual", "active", str(epoch(dt.date(2026, 10, 19))), "stripe"),  # 7 days: not yet
        (5, "annual", "active", str(epoch(dt.date(2026, 10, 11))), "stripe"),  # yesterday: past
        (6, "monthly", "active", "2026-10-12", "web"),                       # today: due
    ]
    conn.executemany(
        "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    db.migrate(conn)
    return conn


def due_customers(conn):
    return sorted(d["customer_id"] for d in due_reminders(conn, TODAY))


def test_existing_stripe_row_is_reminded():
    assert 1 in due_customers(prod_like_db())


def test_window_boundaries_hold_for_both_sources():
    assert due_customers(prod_like_db()) == [1, 2, 6]


def test_new_stripe_subscription_is_reminded():
    conn = sqlite3.connect(":memory:")
    db.migrate(conn)
    conn.execute("INSERT INTO customers VALUES (9, 'c9@x', 'C9')")
    handle_subscription_updated(conn, {"data": {"object": {
        "metadata": {"customer_id": "9"}, "plan": {"interval": "year"},
        "status": "active", "current_period_end": OCT15}}})
    assert due_customers(conn) == [9]


def test_stripe_reminder_is_sent_once(tmp_path, monkeypatch):
    monkeypatch.setenv("MAILER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    conn = prod_like_db()
    assert send_due(conn, TODAY) == 3
    assert send_due(conn, TODAY) == 0
