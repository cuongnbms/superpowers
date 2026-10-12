"""Renewal reminders: one email per renewal, when it is less than 7 days away."""
import argparse
import datetime as dt

from app import db, mailer

WINDOW_DAYS = 7
BATCH = 500


def due_reminders(conn, today):
    """Active subscriptions renewing in [today, today + 7 days) that were not reminded for that renewal."""
    cutoff = today + dt.timedelta(days=WINDOW_DAYS)
    rows = conn.execute(
        """
        SELECT s.id, s.customer_id, c.email, s.renews_at
        FROM subscriptions s
        JOIN customers c ON c.id = s.customer_id
        LEFT JOIN reminder_log r ON r.subscription_id = s.id AND r.renews_at = s.renews_at
        WHERE s.status = 'active'
          AND s.renews_at >= ? AND s.renews_at < ?
          AND r.subscription_id IS NULL
        ORDER BY s.renews_at
        LIMIT ?
        """,
        (today.isoformat(), cutoff.isoformat(), BATCH),
    ).fetchall()
    return [{"subscription_id": r[0], "customer_id": r[1], "email": r[2], "renews_at": r[3]} for r in rows]


def send_due(conn, today):
    sent = 0
    for d in due_reminders(conn, today):
        mailer.send(d["email"], "Your subscription renews soon", f"It renews on {d['renews_at']}.")
        conn.execute(
            "INSERT INTO reminder_log (subscription_id, renews_at, sent_at) VALUES (?, ?, ?)",
            (d["subscription_id"], d["renews_at"], today.isoformat()),
        )
        sent += 1
    conn.commit()
    return sent


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="database file, or 'replica'")
    p.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today())
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    conn = db.connect(args.db)
    if args.dry_run:
        due = due_reminders(conn, args.date)
        for d in due:
            print(f"sub={d['subscription_id']} customer={d['customer_id']} renews_at={d['renews_at']} {d['email']}")
        print(f"{len(due)} due on {args.date}")
        return
    if args.db == "replica":
        raise SystemExit("the replica is read-only; use --dry-run")
    print(f"sent {send_due(conn, args.date)}")


if __name__ == "__main__":
    main()
