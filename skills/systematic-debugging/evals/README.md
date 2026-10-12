# systematic-debugging evals

Two cases in `evals.json`, both on the same small service (`renewals`: nightly renewal reminders, a Stripe webhook, a read-only snapshot of production behind `ops/replica.py`). Each run gets its own copy, built by a setup script that also generates the snapshot (`grading/<case>/make_replica.py`) and a short git history. `grading/` is never copied into a run directory.

- **Case 0, fix-from-prod-evidence** (`fixtures/reminders`). The ticket names a customer; the cause (Stripe sync stores epoch seconds in an ISO-date column) is visible both in the code and in the snapshot. Scored from disk by `scripts/score_reminders.py`: replica reads before the first code edit (`ops/.audit.log`), red before the fix (`.pytest_runs.log` from the fixture's `conftest.py`, edit times from `scripts/watch.py`), the run's tests against the original code, a dry run after the last edit, and 4 hidden acceptance tests that accept either a write-side fix with a migration or a read-side fix.
- **Case 1, diagnose-where-code-and-data-disagree** (`fixtures/reminders-missed`). Diagnosis only, no customer named, and the replica commands live in `docs/runbook.md`, not the README. The code still has the Stripe epoch bug, but those subscriptions renew in 2027; the snapshot shows the real cause (the nightly job fails on one malformed address and aborts the batch). `scripts/score_missed.py` lists replica reads and whether `job_runs` was queried; the reply is graded by hand.

The fixtures need Python 3.8+ and `pytest`; the scripts use the standard library only.

## Running a case

1. Make a workspace outside the repo with one run directory per run:
   `for i in 1 2 3 4 5; do bash scripts/setup_reminders.sh $W/runs/new$i; done`
   (`setup_reminders_missed.sh` for case 1; run names may carry an arm prefix: `new1`, `old1`, `base1`).
2. Case 0 only: start the watcher after every run directory exists and before the first agent starts:
   `python3 scripts/watch.py $W/runs $W/events.json 3600 &`
   It snapshots the directories once at startup and rewrites `events.json` on every tick, so use a new workspace per round.
3. Dispatch one fresh subagent per run with the case's `query`, `<repo>` replaced by the run directory. With-skill runs get this prefix:
   `Before you start, read the skill file <path>/SKILL.md and follow it while you work, including any file it tells you to read.`
   Copy the skill directory into the workspace first, so later edits do not change a running arm. Baseline runs get no prefix.
4. Score after every agent has reported: `python3 scripts/score_reminders.py $W` or `python3 scripts/score_missed.py $W`.

## Harness notes

- Agents usually write a test and the fix in one command, so the first-edit order alone does not show red before the fix; `red<fix` needs a failing pytest run between the two.
- Case 0 hits the ceiling for every arm on hidden tests, replica reads and the rerun; it guards against regressions. Case 1 discriminates on the answer, and case 0 on red before the fix.
- Case 1's snapshot shows the cause in one query (`job_runs` holds the traceback), so it measures whether the agent looks at the record of the failure and checks a candidate cause against the reported customers, not how well it digs.
