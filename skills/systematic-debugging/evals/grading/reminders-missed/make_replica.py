"""Build the reminders-missed fixture's prod snapshot (ops/replica.sqlite).

usage: python3 make_replica.py <fixture-copy>

Since 2026-10-08 the nightly job crashes: customer 1003's address was edited on
2026-10-07 to 'm.alvarez@mail.example ' (trailing space), mailer.send raises on
it, and send_due commits only at the end. Due customers with a lower id get the
email every night without it being logged; everyone after 1003 gets nothing.
Stripe rows still store epoch seconds (a real bug), but they renew in 2027, so
they are not why anyone missed a reminder this month.
"""
import datetime as dt
import os
import random
import sqlite3
import sys

TODAY = dt.date(2026, 10, 12)
BAD_ID, BAD_EMAIL, BAD_RENEWS = 1003, "m.alvarez@mail.example ", dt.date(2026, 10, 14)
FIRST_CRASH = dt.date(2026, 10, 8)


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
    subs = []  # (id, customer_id, status, renews)
    for cid in range(1001, 1221):
        email = BAD_EMAIL if cid == BAD_ID else f"user{cid}@mail.example"
        conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (cid, email, f"User {cid}"))
        renews = BAD_RENEWS if cid == BAD_ID else TODAY + dt.timedelta(days=rnd.randint(0, 34))
        if cid in (1001, 1002):
            renews = dt.date(2026, 10, 15) if cid == 1001 else dt.date(2026, 10, 16)
        status = "active" if cid == BAD_ID or rnd.random() > 0.08 else "cancelled"
        sid = conn.execute(
            "INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) VALUES (?, ?, ?, ?, 'web')",
            (cid, "monthly" if rnd.random() < 0.85 else "annual", status, renews.isoformat()),
        ).lastrowid
        subs.append((sid, cid, status, renews))
        prev = renews - dt.timedelta(days=30)
        if status == "active" and prev < TODAY:  # the previous renewal was reminded on time
            conn.execute("INSERT INTO reminder_log VALUES (?, ?, ?)",
                         (sid, prev.isoformat(), (prev - dt.timedelta(days=6)).isoformat()))
    for i in range(24):
        cid = 1221 + i
        conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (cid, f"user{cid}@mail.example", f"User {cid}"))
        renews = dt.date(2027, 9, 3) + dt.timedelta(days=rnd.randint(0, 38))
        epoch = int(dt.datetime(renews.year, renews.month, renews.day, tzinfo=dt.timezone.utc).timestamp())
        conn.execute("INSERT INTO subscriptions (customer_id, plan, status, renews_at, source) "
                     "VALUES (?, 'annual', 'active', ?, 'stripe')", (cid, epoch))
    # replay the nightly job from 2026-09-14 up to last night
    night = dt.date(2026, 9, 14)
    logged = set()
    while night < TODAY:
        due = [s for s in subs if s[2] == "active" and night <= s[3] < night + dt.timedelta(days=7)
               and (s[0], s[3]) not in logged]
        due.sort()
        start = dt.datetime.combine(night, dt.time(2, 0, rnd.randint(0, 9)))
        if night >= FIRST_CRASH and any(s[1] == BAD_ID for s in due):
            detail = ("Traceback (most recent call last):\n"
                      '  File "/srv/renewals/app/reminders.py", line 34, in send_due\n'
                      '    mailer.send(d["email"], "Your subscription renews soon", f"It renews on {d[\'renews_at\']}.")\n'
                      '  File "/srv/renewals/app/mailer.py", line 12, in send\n'
                      f"    raise ValueError(f\"invalid address {{to!r}}\")\nValueError: invalid address {BAD_EMAIL!r}")
            conn.execute("INSERT INTO job_runs (job, started_at, finished_at, status, detail) VALUES (?, ?, ?, 'failed', ?)",
                         ("reminders", start.isoformat(" "), (start + dt.timedelta(seconds=2)).isoformat(" "), detail))
        else:
            for s in due:
                conn.execute("INSERT INTO reminder_log VALUES (?, ?, ?)", (s[0], s[3].isoformat(), night.isoformat()))
                logged.add((s[0], s[3]))
            conn.execute("INSERT INTO job_runs (job, started_at, finished_at, status, detail) VALUES (?, ?, ?, 'ok', ?)",
                         ("reminders", start.isoformat(" "), (start + dt.timedelta(seconds=3)).isoformat(" "), f"sent {len(due)}"))
        night += dt.timedelta(days=1)
    conn.commit()
    conn.execute("VACUUM")
    conn.close()


if __name__ == "__main__":
    main()
