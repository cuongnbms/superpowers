import datetime as dt

from app.reminders import due_reminders, send_due
from tests.helpers import add_customer, fresh_db

TODAY = dt.date(2026, 10, 12)


def add_sub(conn, cid, renews_at, status="active", plan="monthly"):
    add_customer(conn, cid)
    return conn.execute(
        "INSERT INTO subscriptions (customer_id, plan, status, renews_at) VALUES (?, ?, ?, ?)",
        (cid, plan, status, renews_at),
    ).lastrowid


def due_ids(conn):
    return [d["customer_id"] for d in due_reminders(conn, TODAY)]


def test_renewal_in_three_days_is_due():
    conn = fresh_db()
    add_sub(conn, 1, "2026-10-15")
    assert due_ids(conn) == [1]


def test_renewal_seven_days_away_is_not_due_yet():
    conn = fresh_db()
    add_sub(conn, 1, "2026-10-19")
    assert due_ids(conn) == []


def test_cancelled_subscription_is_not_reminded():
    conn = fresh_db()
    add_sub(conn, 1, "2026-10-15", status="cancelled")
    assert due_ids(conn) == []


def test_reminder_is_sent_once_per_renewal(tmp_path, monkeypatch):
    monkeypatch.setenv("MAILER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    conn = fresh_db()
    add_sub(conn, 1, "2026-10-15")
    assert send_due(conn, TODAY) == 1
    assert send_due(conn, TODAY) == 0
