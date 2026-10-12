#!/usr/bin/env bash
# Make one run directory for the reminders case: a copy of the fixture, its prod
# snapshot, and a git history in which Stripe sync arrived on 2026-09-02.
# usage: bash setup_reminders.sh <run-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$1"
mkdir -p "$DEST"
command cp -R "$HERE/fixtures/reminders/." "$DEST/"
cd "$DEST"
python3 "$HERE/grading/reminders/make_replica.py" "$DEST"
printf '%s\n' '__pycache__/' '.pytest_cache/' '.pytest_runs.log' 'ops/.audit.log' 'ops/replica.sqlite' 'outbox.jsonl' > .gitignore
git init -q -b main
git config user.email dev@renewals.example
git config user.name "Renewals Dev"
commit() { GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
git add .gitignore README.md conftest.py app/__init__.py app/db.py app/billing.py app/mailer.py app/reminders.py \
  migrations ops/__init__.py ops/replica.py tests/__init__.py tests/helpers.py tests/test_billing.py tests/test_reminders.py
commit "2026-06-20T10:00:00+07:00" "feat: nightly renewal reminders"
git add app/stripe_sync.py tests/test_stripe_sync.py
commit "2026-09-02T16:40:00+07:00" "feat(billing): sync subscriptions bought through Stripe"
git status --porcelain | grep . && { echo "setup left untracked files" >&2; exit 1; } || true
