# test-driven-development evals

Three cases in `evals.json`. Cases 0 and 2 run an agent in a copy of a fixture and are scored from what happened on disk; case 1 is a forced choice graded by its first line.

The fixtures and graders need Python 3.8+ and `pytest` (the fixtures are pytest projects; the scripts themselves use the standard library only).

## Running a case

1. Make a workspace outside the repo with one copy of the fixture per run:
   `mkdir -p $W/runs && for i in 1 2 3 4 5; do cp -r fixtures/pricing $W/runs/new$i; done`
   (run names may carry an arm prefix: `new1`, `old1`, `base1`).
2. Start the watcher **after** every run directory exists and **before** the first agent starts:
   `python3 scripts/watch.py $W/runs $W/events.json 2400 &`
   It snapshots the directories once at startup and rewrites `events.json` on every tick, so pointing it at a workspace with earlier results wipes their timing data. Use a new workspace per round.
3. Dispatch one fresh subagent per run with the case's `query`, `<repo>` replaced by the run directory. With-skill runs get this prefix:
   `Before you start, read the skill file <path>/SKILL.md and follow it while you work, including any file it tells you to read.`
   Case 1 uses: `First read the skill file <path>/SKILL.md; it is the skill you follow for this work.`
   Baseline runs get no prefix.
4. Score after every agent has reported (a run scored mid-flight can show a red final state):
   `python3 scripts/score_hotfix.py $W` or `python3 scripts/score_pricing.py $W`.

`fixtures/*/conftest.py` appends one line per pytest run to `.pytest_runs.log`; the scorers read it for red and green runs. `grading/` (hidden acceptance tests, the reference implementation, 12 mutants) is never copied into a run directory.

## Harness notes

- `cp` aliased to `cp -i` in the agent's shell makes an in-place "break the code, then restore" loop hang on the overwrite prompt and leave mutations behind. One run did this and shipped code that failed the hidden tests; the "no mutation left behind" expectation catches it.
- Case 0's test-first and red-before-fix columns hit the ceiling for every skill arm; it guards against regressions, it does not discriminate between skill texts. Case 2 does.
