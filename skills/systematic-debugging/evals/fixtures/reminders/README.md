# renewals

Sends renewal reminder emails for subscriptions. Customers subscribe on the web
(`app/billing.py`) or through Stripe (`app/stripe_sync.py`, webhook handler).
`app/reminders.py` runs every night from the scheduler and emails each customer
whose renewal is less than 7 days away, once per renewal.

## Development

    python3 -m pytest -q

Migrations live in `migrations/NNN_name.sql`. `app.db.connect()` applies the
pending ones in order, which is also how deploys apply them.

## Ops

Last night's snapshot of the production database is available read-only
(access is audited):

    python3 ops/replica.py "SELECT count(*) FROM subscriptions"

To see what tonight's job would send, without sending anything:

    python3 -m app.reminders --db replica --date 2026-10-12 --dry-run

The dry run works on a temporary copy of the snapshot with pending migrations
applied, as a deploy would.
