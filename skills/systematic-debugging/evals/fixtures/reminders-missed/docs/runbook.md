# Runbook

## Production data

Last night's snapshot of the production database is available read-only
(access is audited). The scheduler records every nightly run in `job_runs`.

    python3 ops/replica.py "SELECT * FROM job_runs ORDER BY id DESC LIMIT 5"

To see what tonight's job would send, without sending anything:

    python3 -m app.reminders --db replica --date 2026-10-12 --dry-run

The dry run works on a temporary copy of the snapshot with pending migrations
applied, as a deploy would.
