---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

A fix is only as good as the evidence for its cause. A cause read out of the code and never checked against what actually happened is a guess, and the code always holds more plausible guesses than real causes. So the work runs in one order: look at what happened, get a signal that shows the bug, find the cause the evidence points to, fix it, and watch the signal flip.

## Look at what happened

Start from the record of the failure itself, before reading code for theories:

- the full error message and stack trace;
- what the system recorded when it failed: logs, error trackers, run history, the database rows involved, captured requests;
- what changed: `git log`, deploys, configuration, edited data.

When the failure happened somewhere you are not (a server, a production database, a user's browser), go to where it happened: a replica, the logs, a read-only query, a host you can reach. If you have no way in, say so and ask your human partner for access or a captured artifact (a log dump, a HAR file, a screenshot with timestamps) instead of concluding from the code.

On shared systems, read before you write. Say before you do anything there with side effects: attaching a debugger to a live process, restarting, creating resources that cost money, sending messages to real people.

## Get a signal on this bug

A **signal** is something you have already run or pulled that shows the reported symptom: a failing test, a script, a curl, a CLI call on a fixture, a query whose rows are the affected cases.

- It shows the symptom that was reported, for the cases that were reported. A real bug you find on the way is not the cause until it explains those cases; check it against them.
- Prefer one you can rerun in seconds. You will run it for every hypothesis and again after the fix.
- For an intermittent bug, raise the reproduction rate (loop it, run it in parallel, add load) until it fails often enough to debug.
- For slowness, measure (timings, a profiler, a query plan) instead of estimating.

If you cannot get one, stop: say what you tried and what would let you reproduce it.

## Find the cause

- When the evidence allows more than one explanation, write them down with what each one predicts, then run the check that tells them apart. Change one thing at a time.
- Compare with something that works: a similar code path, the previous version, another environment. List every difference.
- When a bad value surfaces deep in a call stack, trace it back to where it first goes wrong and fix it there; [root-cause-tracing.md](root-cause-tracing.md) has the technique.

The cause is found when it explains every reported case and the signal confirms it, not when the code makes it plausible.

## Fix and verify

1. Turn the signal into a regression test at a seam where the bug actually happens. Run it on the unfixed code and watch it fail with the bug's symptom. A test that fails because a function does not exist yet, or that passes against a mock while the real path stays broken, proves nothing about this bug. If no seam reaches the bug, say so; that is a finding.
2. Fix the cause, in one change, with nothing unrelated.
3. Run the test, the whole suite, and the original signal: the scenario that was reported. A green unit test is not the same as the bug being gone.
4. Remove what you added to investigate: probes, temporary scripts, debug logs, test containers and databases.

## When it is not a code bug

The evidence may say the code works as designed, or the cause is an external service, the data, or the environment. Report that with the evidence and stop; add handling (a retry, an alert, a clearer error) only if your human partner wants it. When you were asked to explain rather than fix, report the cause and its evidence and stop there.

## Report

State the cause and the evidence that confirms it, what you changed, how you verified it (which signal, before and after), what you did not verify, and any side effects on shared systems.

## Techniques

- [condition-based-waiting.md](condition-based-waiting.md): a test or reproduction that depends on timing (sleeps, polling, flakiness).
- [defense-in-depth.md](defense-in-depth.md): after the fix, when invalid data passed through several layers before it failed.
- `find-polluter.sh`: a test run leaves a file or directory behind and you need to know which test (npm projects); usage in root-cause-tracing.md.
